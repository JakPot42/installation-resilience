"""worldbank.py — live World Bank Open Data client for allied-nation
energy vulnerability screening.

Two real, live, no-key World Bank indicators:
  EG.IMP.CONS.ZS  Energy imports, net (% of energy use) -- negative means
                  a net exporter.
  EG.FEC.RNEW.ZS  Renewable energy consumption (% of total final energy
                  consumption).
Both confirmed live and working during this build for 7 countries (see
README). Used live by default; falls back to the exact bundled values
fetched during the build if the network call fails or an indicator has no
recent data for a given country (World Bank indicators commonly lag 1-4
years and have real gaps for some countries -- both are surfaced with the
actual data year, never silently backfilled).
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
IND_ENERGY_IMPORTS = "EG.IMP.CONS.ZS"
IND_RENEWABLE_SHARE = "EG.FEC.RNEW.ZS"

# ISO3 codes for common U.S. security partners -- extend freely, any valid
# ISO3 works against the live API.
COUNTRY_ALIASES: dict[str, str] = {
    "japan": "JPN", "poland": "POL", "philippines": "PHL", "south korea": "KOR",
    "korea": "KOR", "germany": "DEU", "australia": "AUS", "taiwan": "TWN",
}

# Bundled fallback -- exact live World Bank responses fetched during this
# build (see README "Data sourcing").
_CACHED_WORLDBANK: dict[str, dict] = {
    "JPN": {"EG.IMP.CONS.ZS": (2023, 87.3), "EG.FEC.RNEW.ZS": (2021, 8.8)},
    "POL": {"EG.IMP.CONS.ZS": (2023, 48.8), "EG.FEC.RNEW.ZS": (2021, 15.2)},
    "PHL": {"EG.IMP.CONS.ZS": (2022, 54.4), "EG.FEC.RNEW.ZS": (2021, 28.0)},
    "KOR": {"EG.IMP.CONS.ZS": (2023, 84.6), "EG.FEC.RNEW.ZS": (2021, 3.6)},
    "DEU": {"EG.IMP.CONS.ZS": (2023, 70.5), "EG.FEC.RNEW.ZS": (2021, 17.6)},
    "AUS": {"EG.IMP.CONS.ZS": (2023, -214.5), "EG.FEC.RNEW.ZS": (2021, 12.3)},
}


@dataclass
class IndicatorValue:
    year: int
    value: float
    source: str   # "live World Bank API" or "cached (fetched during build)"


def resolve_iso3(country: str) -> str:
    key = country.strip().lower()
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    if len(country) == 3 and country.isalpha():
        return country.upper()
    raise ValueError(
        f"Unknown country '{country}'. Use an ISO3 code (e.g. JPN) or one "
        f"of: {sorted(COUNTRY_ALIASES)}"
    )


def _fetch_live(iso3: str, indicator: str, timeout: float = 10.0) -> IndicatorValue | None:
    resp = requests.get(
        f"{WORLD_BANK_BASE}/country/{iso3}/indicator/{indicator}",
        params={"format": "json", "per_page": 15, "date": "2010:2023"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    rows = [r for r in data[1] if r["value"] is not None]
    if not rows:
        return None
    return IndicatorValue(year=int(rows[0]["date"]), value=float(rows[0]["value"]), source="live World Bank API")


def get_indicator(country: str, indicator: str, use_live: bool = True) -> IndicatorValue:
    iso3 = resolve_iso3(country)
    if use_live:
        try:
            result = _fetch_live(iso3, indicator)
            if result is not None:
                return result
        except Exception:
            pass
    cached = _CACHED_WORLDBANK.get(iso3, {}).get(indicator)
    if cached is None:
        raise ValueError(f"No live or cached World Bank data for {iso3}/{indicator}.")
    year, value = cached
    return IndicatorValue(year=year, value=value, source="cached (fetched live from World Bank during build; see README)")
