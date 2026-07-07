"""brief.py — Claude synthesis for the SMR siting brief and the allied
energy vulnerability brief. Same doctrine as every Claude call site in
this portfolio: every number is computed deterministically upstream
(smr_screener.py / ally_screener.py) -- Claude only narrates already-
computed numbers into plain English, never invents or adjusts one.
DEMO_MODE (default) uses a deterministic template, no API key needed.
"""
from __future__ import annotations

from claude_brief import call_claude

from . import config
from .ally_screener import AllyScreenResult
from .smr_screener import SmrScreenResult


def _smr_template(r: SmrScreenResult) -> str:
    lines = [
        f"DoD INSTALLATION SMR SITING SCREEN -- {r.display_name}",
        "=" * 72,
        config.SCOPE_DISCLAIMER,
        "",
        f"SITING PRIORITY SCORE: {r.total_score}/100 -- {r.tier}",
        "",
        "SCORE COMPONENTS:",
    ]
    for c in r.components:
        lines.append(f"  {c.name}: {c.points}/{c.max_points} -- {c.basis}")
    if r.grid_context is None:
        lines.append("  Regional grid resilience value: EXCLUDED -- installation's state isn't one of "
                      "GridPulse's 6 currently-covered regions (CAL/TEX/MIDA/MIDW/NE/NY); score "
                      "rescaled to the remaining components rather than penalized for a data gap.")
    lines += [
        "",
        f"INSTALLATION ENERGY DEMAND: {r.installation_demand_mwh:,.0f} MWh/yr total site energy "
        f"(all fuels, FY2014 -- {r.energy_citation})",
        "",
        "SMR MODULE OUTPUT vs. INSTALLATION DEMAND (single project, continuous operation, "
        f"{config.NUCLEAR_CAPACITY_FACTOR:.0%} capacity factor):",
    ]
    for f in r.module_fits:
        lines.append(f"  {f.vendor} {f.configuration} ({f.total_mwe:.0f} MWe): "
                      f"{f.annual_output_mwh:,.0f} MWh/yr -- {f.output_to_demand_ratio:.1f}x this installation's demand")
    lines += [
        "",
        "Even the smallest module considered here vastly exceeds a single installation's own "
        "demand -- the real siting question is regulatory/engineering fit (seismic, EPZ, land) "
        "and regional grid value, not raw demand-matching. Excess generation would be a grid-export "
        "resource, not a sizing problem.",
        "",
        f"Location: {r.location_citation}",
        f"Nearest population center: {r.population_citation}",
    ]
    return "\n".join(lines)


def _ally_template(r: AllyScreenResult) -> str:
    return "\n".join([
        f"ALLIED NATION ENERGY VULNERABILITY SCREEN -- {r.country}",
        "=" * 72,
        config.SCOPE_DISCLAIMER,
        "",
        f"VULNERABILITY SCORE: {r.score}/100 -- {r.tier}",
        "",
        f"Energy import dependency: {r.import_dependency_pct:.1f}% of energy use ({r.import_year}) "
        f"-- {r.import_source}",
        f"Renewable energy share: {r.renewable_share_pct:.1f}% of final consumption ({r.renewable_year}) "
        f"-- {r.renewable_source}",
        "",
        "Score = import_dependency (clamped 0-100) x 70% + (100 - renewable_share) x 30% -- "
        "disclosed weights, not a published DoD formula (none found in this build's research; "
        "see README).",
        "",
        "A negative import-dependency figure means the country is a net energy EXPORTER -- "
        "scored as zero import vulnerability by this measure, not treated as a data error.",
    ])


_SMR_SYSTEM_PROMPT = (
    "You write a short, plain-English DoD installation SMR siting screen from pre-computed, "
    "deterministic inputs. Rules, mandatory: (1) never invent, adjust, or round a number "
    "differently than given. (2) never state or imply this is a final siting recommendation "
    "or regulatory determination -- it is a screening priority score for further study. "
    "(3) always mention that module output vastly exceeds a single installation's demand, and "
    "that excess generation is a potential grid-export resource, not a sizing failure. "
    "(4) if a score component is marked EXCLUDED, say so plainly -- don't imply the region was "
    "scored zero. Output plain text, no markdown headers, under 300 words."
)

_ALLY_SYSTEM_PROMPT = (
    "You write a short, plain-English allied-nation energy vulnerability screen from pre-computed "
    "deterministic inputs (World Bank import-dependency and renewable-share indicators). Rules, "
    "mandatory: (1) never invent or adjust a number. (2) never make a policy or alliance "
    "recommendation -- describe the energy exposure only. (3) note the data year for each "
    "indicator since World Bank data lags real-time. (4) if import dependency is negative, "
    "explain that means a net exporter, not a data error. Output plain text, no markdown "
    "headers, under 250 words."
)


def generate_smr_brief(r: SmrScreenResult) -> str:
    template = _smr_template(r)
    if config.DEMO_MODE:
        return template
    return call_claude(
        [{"role": "user", "content": template}],
        system=_SMR_SYSTEM_PROMPT,
        max_tokens=600,
        model=config.CLAUDE_MODEL,
        on_error="fallback",
        fallback=template,
    )


def generate_ally_brief(r: AllyScreenResult) -> str:
    template = _ally_template(r)
    if config.DEMO_MODE:
        return template
    return call_claude(
        [{"role": "user", "content": template}],
        system=_ALLY_SYSTEM_PROMPT,
        max_tokens=600,
        model=config.CLAUDE_MODEL,
        on_error="fallback",
        fallback=template,
    )
