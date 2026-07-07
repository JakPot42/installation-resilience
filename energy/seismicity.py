"""seismicity.py — live USGS seismic design-value client.

The USGS Design Ground Motions web service (earthquake.usgs.gov/ws/
designmaps) computes real ASCE 7 seismic design parameters (including
Seismic Design Category, SDC, the standard A-F engineering classification
building codes use) for any lat/lon -- no API key, no authentication.
Confirmed live and working for all 4 roster installations during this
build (see README). Used live by default; falls back to a bundled cache
of the exact values fetched during the build if the network call fails,
same "real live API, cached fallback for demo reliability" pattern as
P18's OOI hydrophone integration.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

USGS_DESIGN_MAPS_URL = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"

# Bundled fallback -- the exact live USGS response fetched for each roster
# installation during this build (see README "Data sourcing"). Used only if
# the live call fails (network unavailable, USGS service down, etc).
_CACHED_SEISMIC: dict[str, dict] = {
    "naval station newport": {"pga_m": 0.11, "sds": 0.16, "sd1": 0.065, "sdc": "A"},
    "naval submarine base kings bay": {"pga_m": 0.091, "sds": 0.16, "sd1": 0.1, "sdc": "B"},
    "edwards air force base": {"pga_m": 0.5, "sds": 0.91, "sd1": 0.61, "sdc": "D"},
    "travis air force base": {"pga_m": 0.63, "sds": 1.09, "sd1": 0.82, "sdc": "D"},
}

# SDC A is the lowest seismic hazard classification, F the highest --
# fewer/simpler seismic-qualification engineering requirements at lower SDC.
SDC_ORDER = ["A", "B", "C", "D", "E", "F"]


@dataclass
class SeismicResult:
    pga_m: float          # MCE-geometric-mean peak ground acceleration (g)
    sds: float             # design spectral acceleration, short period (g)
    sd1: float              # design spectral acceleration, 1-second period (g)
    sdc: str                # Seismic Design Category, A (lowest hazard) - F (highest)
    source: str              # "live USGS ws/designmaps" or "cached (fetched during build)"


def fetch_live(lat: float, lon: float, risk_category: str = "III", site_class: str = "D", timeout: float = 10.0) -> SeismicResult:
    resp = requests.get(
        USGS_DESIGN_MAPS_URL,
        params={"latitude": lat, "longitude": lon, "riskCategory": risk_category, "siteClass": site_class},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()["response"]["data"]
    return SeismicResult(
        pga_m=data["pgam"], sds=data["sds"], sd1=data["sd1"], sdc=data["sdc"],
        source="live USGS ws/designmaps (ASCE 7-22)",
    )


def get_seismic_design(installation_key: str, lat: float, lon: float, use_live: bool = True) -> SeismicResult:
    if use_live:
        try:
            return fetch_live(lat, lon)
        except Exception:
            pass
    cached = _CACHED_SEISMIC.get(installation_key)
    if cached is None:
        raise ValueError(f"No cached seismic data for '{installation_key}' and live fetch unavailable.")
    return SeismicResult(**cached, source="cached (fetched live from USGS during build; see README)")
