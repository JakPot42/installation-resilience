"""eroei.py — Installation EROEI (Energy Return on Energy Invested)
lookup and installation-context arithmetic.

EROEI values come straight from config.EROEI_SOURCES (real cited peer-
reviewed/compilation figures) -- this module does no estimation of its
own for the EROEI number itself. `--context installation` adds one piece
of deterministic, fully-transparent arithmetic: how a source's typical
generation project output compares to a real installation's real energy
demand. That comparison is arithmetic on cited numbers, not a new claim
about the source's efficiency.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass
class EroeiResult:
    source_key: str
    label: str
    eroi_low: float
    eroi_high: float
    citation: str
    installation_context: str | None = None


def list_sources() -> list[str]:
    return sorted(config.EROEI_SOURCES.keys())


def get_eroei(source: str, installation_key: str | None = None) -> EroeiResult:
    key = source.strip().lower().replace(" ", "_").replace("-", "_")
    entry = config.EROEI_SOURCES.get(key)
    if entry is None:
        raise ValueError(f"Unknown source '{source}'. Available: {', '.join(list_sources())}")

    context = None
    if installation_key is not None:
        inst_key = installation_key.strip().lower()
        inst = config.INSTALLATIONS.get(inst_key)
        if inst is None:
            raise ValueError(
                f"'{installation_key}' is not in joule's installation roster. "
                f"Supported: {', '.join(i['display_name'] for i in config.INSTALLATIONS.values())}"
            )
        demand_mwh = inst["fy2014_site_energy_bbtu"] * config.BBTU_TO_MWH
        context = (
            f"EROEI describes energy return per unit invested, not project size -- "
            f"it doesn't directly convert to '{inst['display_name']}'s demand of "
            f"{demand_mwh:,.0f} MWh/yr (FY2014 total site energy, {inst['energy_citation']}).' "
            f"What the two numbers together DO show: for nuclear-class EROEI sources "
            f"(EROI {config.EROEI_SOURCES['nuclear']['eroi_low']}-"
            f"{config.EROEI_SOURCES['nuclear']['eroi_high']}), even the smallest SMR "
            f"module considered in `joule smr` (77 MWe) would need to run for only "
            f"~{demand_mwh / (77 * 8760 * config.NUCLEAR_CAPACITY_FACTOR) * 365:.1f} days/year "
            f"to cover the installation's entire site energy demand -- see `joule smr "
            f"{installation_key}` for the full siting picture."
        )

    return EroeiResult(
        source_key=key, label=entry["label"], eroi_low=entry["eroi_low"],
        eroi_high=entry["eroi_high"], citation=entry["citation"],
        installation_context=context,
    )
