"""ally_screener.py — Allied Nation Energy Vulnerability Screener.

Deterministic scoring from two live World Bank indicators (worldbank.py):
  - Energy import dependency (0-70 pts): net energy imports as % of energy
    use, clamped to [0,100] (net exporters score 0 here -- they aren't
    import-vulnerable by this measure).
  - Renewable energy share (0-30 pts, inverse): lower domestic renewable
    share scores higher here, as a disclosed proxy for diversification
    away from imports -- NOT a claim that renewables are the only
    domestic energy resource a country might have (nuclear, coal, gas
    production also reduce import dependency and are already captured
    directly by the import-dependency indicator itself).
Weights (70/30) are disclosed, not derived from a published DoD formula --
no such public formula was found in this build's research; see README.
"""
from __future__ import annotations

from dataclasses import dataclass

from .worldbank import IND_ENERGY_IMPORTS, IND_RENEWABLE_SHARE, get_indicator

IMPORT_WEIGHT = 0.70
RENEWABLE_WEIGHT = 0.30

TIERS = [
    (75.0, "HIGH VULNERABILITY"),
    (55.0, "ELEVATED VULNERABILITY"),
    (30.0, "MODERATE VULNERABILITY"),
    (0.0, "LOW VULNERABILITY"),
]


@dataclass
class AllyScreenResult:
    country: str
    import_dependency_pct: float
    import_year: int
    import_source: str
    renewable_share_pct: float
    renewable_year: int
    renewable_source: str
    score: float
    tier: str


def _tier_for(score: float) -> str:
    for threshold, label in TIERS:
        if score >= threshold:
            return label
    return TIERS[-1][1]


def screen_country(country: str, use_live: bool = True) -> AllyScreenResult:
    imp = get_indicator(country, IND_ENERGY_IMPORTS, use_live=use_live)
    ren = get_indicator(country, IND_RENEWABLE_SHARE, use_live=use_live)

    import_clamped = max(0.0, min(100.0, imp.value))
    renewable_clamped = max(0.0, min(100.0, ren.value))

    import_points = import_clamped * IMPORT_WEIGHT
    renewable_points = (100.0 - renewable_clamped) * RENEWABLE_WEIGHT
    score = round(import_points + renewable_points, 1)

    return AllyScreenResult(
        country=country,
        import_dependency_pct=imp.value, import_year=imp.year, import_source=imp.source,
        renewable_share_pct=ren.value, renewable_year=ren.year, renewable_source=ren.source,
        score=score, tier=_tier_for(score),
    )
