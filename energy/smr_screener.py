"""smr_screener.py — DoD Installation SMR Siting Priority Score.

Deterministic scoring only -- no Claude in this module. Four disclosed,
weighted components, each traceable to a real data source:

  1. Seismic siting fitness   (0-35 pts) -- live USGS Seismic Design
     Category (SDC). Lower SDC = fewer/simpler seismic-qualification
     engineering requirements.
  2. Regional grid resilience value (0-30 pts) -- GridPulse grid
     stress tier for the installation's region, when covered. A
     HIGH/CRITICAL-stress region gets more resilience value from an
     on-site SMR (it can't easily absorb losing grid power); excluded
     (not zeroed) from the score when GridPulse doesn't cover the
     installation's region, and the total is rescaled to the remaining
     components rather than silently penalized.
  3. Population-proximity siting simplicity (0-20 pts) -- real 2020
     Census population of the nearest population center. Smaller nearby
     population = fewer public/regulatory engagement friction points at
     initial siting (this is a simplification -- it is NOT the same as
     the formal NRC Emergency Planning Zone determination, which for
     both designs here is claimed at or near the site boundary already;
     see config.SMR_DESIGNS).
  4. Installation energy-demand magnitude (0-15 pts) -- real FY2014 DoD
     AEMR total site energy (BBTU), scaled against a fixed 0-1000 BBTU
     reference band (a large, but not maximal, DoD installation) rather
     than relative to just this roster, so the score doesn't shift if
     more installations are added later.

This produces a SITING PRIORITY score, not a suitability certification or
regulatory determination -- see config.SCOPE_DISCLAIMER.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .gridpulse_bridge import GridStressContext, get_grid_context
from .seismicity import SeismicResult, get_seismic_design

SDC_POINTS = {"A": 35, "B": 28, "C": 18, "D": 8, "E": 3, "F": 0}
GRID_TIER_POINTS = {"LOW": 5, "ELEVATED": 15, "HIGH": 25, "CRITICAL": 30}
DEMAND_REFERENCE_BBTU = 1000.0   # 0-15 pt scale anchor; see module docstring


@dataclass
class ScoreComponent:
    name: str
    points: float
    max_points: float
    basis: str


@dataclass
class ModuleFit:
    design_key: str
    vendor: str
    design_name: str
    configuration: str
    module_count: int
    total_mwe: float
    annual_output_mwh: float
    installation_demand_mwh: float
    output_to_demand_ratio: float


@dataclass
class SmrScreenResult:
    installation_key: str
    display_name: str
    seismic: SeismicResult
    grid_context: GridStressContext | None
    components: list[ScoreComponent]
    total_score: float
    tier: str
    module_fits: list[ModuleFit]
    installation_demand_mwh: float
    energy_citation: str
    location_citation: str
    population_citation: str


def _population_points(population: int) -> tuple[float, str]:
    if population < 20_000:
        return 20.0, f"< 20,000 (nearest center: {population:,})"
    if population < 50_000:
        return 15.0, f"20,000-50,000 (nearest center: {population:,})"
    if population < 150_000:
        return 10.0, f"50,000-150,000 (nearest center: {population:,})"
    return 5.0, f">= 150,000 (nearest center: {population:,})"


def _demand_points(bbtu: float) -> tuple[float, str]:
    pts = min(15.0, round(15.0 * bbtu / DEMAND_REFERENCE_BBTU, 1))
    return pts, f"{bbtu:,.0f} BBtu/yr total site energy (FY2014), vs. {DEMAND_REFERENCE_BBTU:,.0f} BBtu/yr reference band"


def compute_module_fits(installation_demand_mwh: float) -> list[ModuleFit]:
    fits = []
    for design_key, design in config.SMR_DESIGNS.items():
        for config_name, module_count in design["configurations"].items():
            total_mwe = design["module_mwe"] * module_count
            annual_output_mwh = total_mwe * 8760 * config.NUCLEAR_CAPACITY_FACTOR
            fits.append(ModuleFit(
                design_key=design_key,
                vendor=design["vendor"],
                design_name=design["design_name"],
                configuration=config_name,
                module_count=module_count,
                total_mwe=total_mwe,
                annual_output_mwh=annual_output_mwh,
                installation_demand_mwh=installation_demand_mwh,
                output_to_demand_ratio=annual_output_mwh / installation_demand_mwh if installation_demand_mwh else float("inf"),
            ))
    return sorted(fits, key=lambda f: f.total_mwe)


def screen_installation(installation_key: str, use_live: bool = True) -> SmrScreenResult:
    key = installation_key.strip().lower()
    inst = config.INSTALLATIONS.get(key)
    if inst is None:
        raise ValueError(
            f"'{installation_key}' is not in joule's installation roster. "
            f"Supported: {', '.join(i['display_name'] for i in config.INSTALLATIONS.values())}"
        )

    seismic = get_seismic_design(key, inst["lat"], inst["lon"], use_live=use_live)
    grid_context = get_grid_context(inst["gridpulse_region"])

    demand_mwh = inst["fy2014_site_energy_bbtu"] * config.BBTU_TO_MWH

    pop_points, pop_basis = _population_points(inst["nearest_population"])
    demand_points, demand_basis = _demand_points(inst["fy2014_site_energy_bbtu"])

    components = [
        ScoreComponent(
            "Seismic siting fitness", SDC_POINTS.get(seismic.sdc, 0), 35.0,
            f"USGS ASCE 7-22 Seismic Design Category {seismic.sdc} (PGA={seismic.pga_m}g, SDS={seismic.sds}g)",
        ),
        ScoreComponent("Population-proximity siting simplicity", pop_points, 20.0, pop_basis),
    ]
    components.append(ScoreComponent("Installation energy-demand magnitude", demand_points, 15.0, demand_basis))

    if grid_context is not None:
        grid_points = GRID_TIER_POINTS.get(grid_context.tier, 0)
        components.append(ScoreComponent(
            "Regional grid resilience value", grid_points, 30.0,
            f"GridPulse region {grid_context.region}: {grid_context.tier} stress "
            f"(score {grid_context.stress_score}, as of {grid_context.hour})",
        ))
    # else: component genuinely excluded, not zeroed -- see module docstring.

    total_earned = sum(c.points for c in components)
    total_possible = sum(c.max_points for c in components)
    total_score = round(100.0 * total_earned / total_possible, 1) if total_possible else 0.0

    if total_score >= 70:
        tier = "PRIORITY FOR FURTHER STUDY"
    elif total_score >= 45:
        tier = "WORTH INVESTIGATING"
    else:
        tier = "LOWER PRIORITY"

    return SmrScreenResult(
        installation_key=key,
        display_name=inst["display_name"],
        seismic=seismic,
        grid_context=grid_context,
        components=components,
        total_score=total_score,
        tier=tier,
        module_fits=compute_module_fits(demand_mwh),
        installation_demand_mwh=demand_mwh,
        energy_citation=inst["energy_citation"],
        location_citation=inst["location_citation"],
        population_citation=inst["population_citation"],
    )
