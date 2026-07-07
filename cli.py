"""
CLI entry point for Installation Resilience (Phase 6, Cluster 5).

Usage:
    python cli.py grid dashboard
    python cli.py grid region TEX
    python cli.py grid brief CAL
    python cli.py grid scenario TEX --scenario wind_drop
    python cli.py grid export --format json
    python cli.py grid demo

    python cli.py water dashboard
    python cli.py water region COLO
    python cli.py water brief CAL
    python cli.py water scenario GPLN --scenario reservoir_low
    python cli.py water export --format json
    python cli.py water demo

    python cli.py energy smr "Naval Station Newport"
    python cli.py energy eroei nuclear --context "Naval Station Newport"
    python cli.py energy eroei-sources
    python cli.py energy ally Japan
    python cli.py energy installations
    python cli.py energy demo
"""
from __future__ import annotations

import click

import grid.dashboard as grid_dashboard
import water.dashboard as water_dashboard
import energy.dashboard as energy_dashboard
import energy.config as energy_config
from grid.pipeline import build_snapshots as grid_build_snapshots, current_snapshot as grid_current_snapshot
from grid.scenarios import run_scenario as grid_run_scenario, run_named_scenario as grid_run_named_scenario, to_joule_format
from grid.brief import generate_brief as grid_generate_brief
from grid.config import DEMO_MODE as GRID_DEMO_MODE, REGIONS as GRID_REGIONS, SCENARIO_DEFAULTS as GRID_SCENARIOS

from water.pipeline import build_snapshots as water_build_snapshots
from water.scenarios import run_scenario as water_run_scenario, run_named_scenario as water_run_named_scenario
from water.brief import generate_brief as water_generate_brief
from water.config import DEMO_MODE as WATER_DEMO_MODE, REGIONS as WATER_REGIONS, SCENARIO_DEFAULTS as WATER_SCENARIOS

from energy.ally_screener import screen_country
from energy.brief import generate_ally_brief, generate_smr_brief
from energy.eroei import get_eroei, list_sources
from energy.smr_screener import screen_installation

_GRID_REGION_CHOICES = sorted(GRID_REGIONS.keys())
_GRID_SCENARIO_CHOICES = sorted(GRID_SCENARIOS.keys())
_WATER_REGION_CHOICES = sorted(WATER_REGIONS.keys())
_WATER_SCENARIO_CHOICES = sorted(WATER_SCENARIOS.keys())


@click.group()
def ir() -> None:
    """Installation Resilience: unified CLI for grid, water, and energy resilience tools.

    \b
    Three subcommand groups mapping 1:1 to the source tools:
      ir grid    -- GridPulse regional grid stress index (EIA + NOAA)
      ir water   -- Water Security Stress Monitor (USGS + USDM)
      ir energy  -- joule DoD Energy Resilience Intelligence Tool
    """


# ---------------------------------------------------------------------------
# ir grid
# ---------------------------------------------------------------------------

@ir.group()
@click.option(
    "--hours", default=6, show_default=True, type=int,
    help="Hours of data to fetch (1-24).",
)
@click.pass_context
def grid(ctx: click.Context, hours: int) -> None:
    """GridPulse: fuses EIA electricity demand with NOAA weather forecasts
    into a regional grid stress index.

    \b
    Set DEMO_MODE=False and EIA_API_KEY to fetch live data.
    """
    ctx.ensure_object(dict)
    ctx.obj["hours"] = hours


@grid.command("dashboard")
@click.option(
    "--region", "-r",
    type=click.Choice(_GRID_REGION_CHOICES, case_sensitive=False),
    multiple=True,
    help="Region(s) to include. Default: all regions.",
)
@click.pass_context
def grid_dashboard_cmd(ctx: click.Context, region: tuple[str, ...]) -> None:
    """Show all-region stress overview for the current hour."""
    grid_dashboard.print_banner()
    regions = list(region) if region else None
    snapshots = grid_build_snapshots(regions=regions, hours=ctx.obj["hours"])
    grid_dashboard.print_dashboard(snapshots)
    if GRID_DEMO_MODE:
        grid_dashboard.console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@grid.command("region")
@click.argument("region", type=click.Choice(_GRID_REGION_CHOICES, case_sensitive=False))
@click.pass_context
def grid_region_cmd(ctx: click.Context, region: str) -> None:
    """Show hourly stress timeline for a single REGION (CAL, TEX, MIDA, MIDW, NE, NY)."""
    grid_dashboard.print_banner()
    snapshots = grid_build_snapshots(regions=[region], hours=ctx.obj["hours"])
    snaps = snapshots.get(region, [])
    if not snaps:
        grid_dashboard.console.print(f"[red]No data returned for {region}.[/red]")
        raise SystemExit(1)
    grid_dashboard.print_region_timeline(region, snaps)
    if GRID_DEMO_MODE:
        grid_dashboard.console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@grid.command("brief")
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_GRID_REGION_CHOICES, case_sensitive=False))
@click.pass_context
def grid_brief_cmd(ctx: click.Context, target_region: str) -> None:
    """Generate a Claude stress-driver brief for REGION."""
    grid_dashboard.print_banner()
    snapshots = grid_build_snapshots(regions=[target_region], hours=ctx.obj["hours"])
    snap = grid_current_snapshot(snapshots.get(target_region, []))
    if snap is None:
        grid_dashboard.console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)
    grid_dashboard.console.print(f"[dim]Generating brief for {target_region} (stress={snap.stress_score:.1f}, tier={snap.tier})...[/dim]")
    text = grid_generate_brief(snap)
    grid_dashboard.print_brief(target_region, text)


@grid.command("scenario")
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_GRID_REGION_CHOICES, case_sensitive=False))
@click.option(
    "--scenario", "-s",
    type=click.Choice(_GRID_SCENARIO_CHOICES),
    default=None,
    help="Named scenario preset (wind_drop, solar_drop, demand_surge, polar_vortex).",
)
@click.option("--wind-pct", type=float, default=None, help="Wind generation change in pct.")
@click.option("--solar-pct", type=float, default=None, help="Solar generation change in pct.")
@click.option("--demand-pct", type=float, default=None, help="Demand change in pct.")
@click.pass_context
def grid_scenario_cmd(
    ctx: click.Context,
    target_region: str,
    scenario: str | None,
    wind_pct: float | None,
    solar_pct: float | None,
    demand_pct: float | None,
) -> None:
    """What-if scenario analysis for REGION."""
    grid_dashboard.print_banner()
    snapshots = grid_build_snapshots(regions=[target_region], hours=ctx.obj["hours"])
    snap = grid_current_snapshot(snapshots.get(target_region, []))
    if snap is None:
        grid_dashboard.console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)

    has_custom = any(v is not None for v in [wind_pct, solar_pct, demand_pct])

    if not has_custom and scenario is None:
        scenario = "wind_drop"

    if has_custom:
        name = scenario or "custom"
        result = grid_run_scenario(
            snap, name,
            wind_pct=wind_pct or 0.0,
            solar_pct=solar_pct or 0.0,
            demand_pct=demand_pct or 0.0,
        )
    else:
        result = grid_run_named_scenario(snap, scenario)

    grid_dashboard.print_scenario(result)
    if GRID_DEMO_MODE:
        grid_dashboard.console.print("[dim]DEMO_MODE=True -- set EIA_API_KEY and DEMO_MODE=False for live data.[/dim]")


@grid.command("export")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", show_default=True)
@click.pass_context
def grid_export_cmd(ctx: click.Context, fmt: str) -> None:
    """Export current-hour stress index in energy (joule) SMR format."""
    snapshots = grid_build_snapshots(hours=ctx.obj["hours"])
    current_snaps = [
        s for region_snaps in snapshots.values()
        for s in [grid_current_snapshot(region_snaps)]
        if s is not None
    ]
    joule_data = to_joule_format(current_snaps)
    if fmt == "json":
        grid_dashboard.print_json(joule_data)
    else:
        grid_dashboard.print_banner()
        grid_dashboard.print_joule_export(joule_data)


@grid.command("demo")
@click.pass_context
def grid_demo_cmd(ctx: click.Context) -> None:
    """Run all GridPulse commands against seeded demo data."""
    grid_dashboard.print_banner()
    grid_dashboard.console.rule("[bold]Demo 1: All-Region Dashboard[/bold]")
    snapshots = grid_build_snapshots(hours=6)
    grid_dashboard.print_dashboard(snapshots)

    grid_dashboard.console.rule("[bold]Demo 2: Texas Hourly Timeline[/bold]")
    grid_dashboard.print_region_timeline("TEX", snapshots["TEX"])

    grid_dashboard.console.rule("[bold]Demo 3: Texas Stress Brief[/bold]")
    tex_snap = grid_current_snapshot(snapshots["TEX"])
    if tex_snap:
        text = grid_generate_brief(tex_snap, demo_mode=True)
        grid_dashboard.print_brief("TEX", text)

    grid_dashboard.console.rule("[bold]Demo 4: Wind Drop Scenario (Texas)[/bold]")
    if tex_snap:
        result = grid_run_named_scenario(tex_snap, "wind_drop")
        grid_dashboard.print_scenario(result)

    grid_dashboard.console.rule("[bold]Demo 5: Polar Vortex Scenario (New England)[/bold]")
    ne_snap = grid_current_snapshot(snapshots["NE"])
    if ne_snap:
        result = grid_run_named_scenario(ne_snap, "polar_vortex")
        grid_dashboard.print_scenario(result)
        ne_brief = grid_generate_brief(ne_snap, demo_mode=True)
        grid_dashboard.print_brief("NE", ne_brief)

    grid_dashboard.console.rule("[bold]Demo 6: Energy (joule) Export Integration[/bold]")
    current_snaps = [
        s for region_snaps in snapshots.values()
        for s in [grid_current_snapshot(region_snaps)]
        if s is not None
    ]
    joule_data = to_joule_format(current_snaps)
    grid_dashboard.print_joule_export(joule_data)

    grid_dashboard.console.print("[dim]All demo output uses seeded data. Set DEMO_MODE=False for live EIA/NOAA data.[/dim]")


# ---------------------------------------------------------------------------
# ir water
# ---------------------------------------------------------------------------

@ir.group()
def water() -> None:
    """Water Security Stress Monitor: fuses USGS streamflow percentiles with
    USDM drought severity into a regional water stress index.

    \b
    CISA NCF framing: Water and Wastewater Systems (NCF-39/40)
    Set DEMO_MODE=False to fetch live data.
    """


@water.command("dashboard")
@click.option(
    "--region", "-r",
    type=click.Choice(_WATER_REGION_CHOICES, case_sensitive=False),
    multiple=True,
    help="Region(s) to include. Default: all regions.",
)
def water_dashboard_cmd(region: tuple[str, ...]) -> None:
    """Show all-region water stress overview."""
    water_dashboard.print_banner()
    regions = list(region) if region else None
    snapshots = water_build_snapshots(regions=regions)
    water_dashboard.print_dashboard(snapshots)
    if WATER_DEMO_MODE:
        water_dashboard.console.print("[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]")


@water.command("region")
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_WATER_REGION_CHOICES, case_sensitive=False))
def water_region_cmd(target_region: str) -> None:
    """Show detailed water stress for REGION (COLO, CAL, SWUS, SPLNS, GPLN, GLAKE, SE, MISS)."""
    water_dashboard.print_banner()
    snapshots = water_build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        water_dashboard.console.print(f"[red]No data returned for {target_region}.[/red]")
        raise SystemExit(1)
    water_dashboard.print_region_detail(snap)
    if WATER_DEMO_MODE:
        water_dashboard.console.print("[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]")


@water.command("brief")
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_WATER_REGION_CHOICES, case_sensitive=False))
def water_brief_cmd(target_region: str) -> None:
    """Generate a Claude stress-driver brief for REGION."""
    water_dashboard.print_banner()
    snapshots = water_build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        water_dashboard.console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)
    water_dashboard.console.print(
        f"[dim]Generating brief for {target_region} "
        f"(stress={snap.stress_score:.1f}, tier={snap.tier})...[/dim]"
    )
    text = water_generate_brief(snap)
    water_dashboard.print_brief(target_region, text)


@water.command("scenario")
@click.argument("target_region", metavar="REGION",
                type=click.Choice(_WATER_REGION_CHOICES, case_sensitive=False))
@click.option("--scenario", "-s", type=click.Choice(_WATER_SCENARIO_CHOICES), default=None, help="Named scenario preset.")
@click.option("--streamflow-delta", type=float, default=None, help="Streamflow percentile delta.")
@click.option("--drought-delta", type=float, default=None, help="Drought index delta.")
@click.option("--reservoir-pct", type=float, default=None, help="Override reservoir storage %.")
def water_scenario_cmd(
    target_region: str,
    scenario: str | None,
    streamflow_delta: float | None,
    drought_delta: float | None,
    reservoir_pct: float | None,
) -> None:
    """What-if scenario analysis for REGION."""
    water_dashboard.print_banner()
    snapshots = water_build_snapshots(regions=[target_region])
    snap = snapshots.get(target_region)
    if snap is None:
        water_dashboard.console.print(f"[red]No data for {target_region}.[/red]")
        raise SystemExit(1)

    has_custom = any(v is not None for v in [streamflow_delta, drought_delta, reservoir_pct])

    if not has_custom and scenario is None:
        scenario = "drought_intensifies"

    if has_custom:
        name = scenario or "custom"
        result = water_run_scenario(
            snap, name,
            streamflow_pctile_delta=streamflow_delta or 0.0,
            drought_index_delta=drought_delta or 0.0,
            reservoir_pct_override=reservoir_pct,
        )
    else:
        result = water_run_named_scenario(snap, scenario)

    water_dashboard.print_scenario(result)
    if WATER_DEMO_MODE:
        water_dashboard.console.print("[dim]DEMO_MODE=True -- set DEMO_MODE=False for live USGS/USDM data.[/dim]")


@water.command("export")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", show_default=True)
def water_export_cmd(fmt: str) -> None:
    """Export current water stress index as JSON (integration-ready format)."""
    snapshots = water_build_snapshots()
    data = {
        region: {
            "stress_score": round(snap.stress_score, 1),
            "tier": snap.tier,
            "streamflow_pctile": snap.streamflow_pctile,
            "drought_index": round(snap.drought_index, 1),
            "supply_stress": round(snap.supply_stress, 1),
            "reservoir_pct": snap.reservoir_pct,
            "date": snap.date,
        }
        for region, snap in snapshots.items()
    }
    if fmt == "json":
        water_dashboard.print_json(data)
    else:
        water_dashboard.print_banner()
        from rich.table import Table
        from rich import box
        t = Table(box=box.SIMPLE, show_header=True)
        t.add_column("Region")
        t.add_column("Score", justify="right")
        t.add_column("Tier")
        t.add_column("Flow Pctile", justify="right")
        t.add_column("Drought Idx", justify="right")
        t.add_column("Reservoir", justify="right")
        for rgn, d in sorted(data.items()):
            color = water_dashboard.TIER_COLORS.get(d["tier"], "white")
            res = f"{d['reservoir_pct']:.0f}%" if d["reservoir_pct"] is not None else "N/A"
            t.add_row(
                rgn,
                f"{d['stress_score']:.1f}",
                f"[{color}]{d['tier']}[/{color}]",
                f"P{d['streamflow_pctile']:.0f}",
                f"{d['drought_index']:.1f}",
                res,
            )
        water_dashboard.console.print(t)


@water.command("demo")
def water_demo_cmd() -> None:
    """Run all WaterMonitor commands against seeded demo data."""
    water_dashboard.print_banner()
    snapshots = water_build_snapshots()

    water_dashboard.console.rule("[bold]Demo 1: All-Region Dashboard[/bold]")
    water_dashboard.print_dashboard(snapshots)

    water_dashboard.console.rule("[bold]Demo 2: Colorado River Basin Detail[/bold]")
    water_dashboard.print_region_detail(snapshots["COLO"])

    water_dashboard.console.rule("[bold]Demo 3: Colorado River Basin Brief[/bold]")
    text = water_generate_brief(snapshots["COLO"], demo_mode=True)
    water_dashboard.print_brief("COLO", text)

    water_dashboard.console.rule("[bold]Demo 4: Drought Intensification Scenario (Colorado)[/bold]")
    result = water_run_named_scenario(snapshots["COLO"], "drought_intensifies")
    water_dashboard.print_scenario(result)

    water_dashboard.console.rule("[bold]Demo 5: Streamflow Collapse Scenario (California)[/bold]")
    result2 = water_run_named_scenario(snapshots["CAL"], "streamflow_collapse")
    water_dashboard.print_scenario(result2)
    cal_brief = water_generate_brief(snapshots["CAL"], demo_mode=True)
    water_dashboard.print_brief("CAL", cal_brief)

    water_dashboard.console.rule("[bold]Demo 6: Great Plains -- LOW Stress Region[/bold]")
    water_dashboard.print_region_detail(snapshots["GPLN"])

    water_dashboard.console.rule("[bold]Demo 7: JSON Export[/bold]")
    data = {
        rgn: {
            "stress_score": round(snap.stress_score, 1),
            "tier": snap.tier,
            "streamflow_pctile": snap.streamflow_pctile,
            "drought_index": round(snap.drought_index, 1),
        }
        for rgn, snap in snapshots.items()
    }
    water_dashboard.print_json(data)

    water_dashboard.console.print("[dim]All demo output uses seeded data. Set DEMO_MODE=False for live USGS/USDM data.[/dim]")


# ---------------------------------------------------------------------------
# ir energy
# ---------------------------------------------------------------------------

@ir.group()
def energy() -> None:
    """joule: DoD Energy Resilience Intelligence Tool.

    \b
    Three modules: `smr` (DoD Installation SMR Suitability Screener),
    `eroei` (Installation EROEI calculator), `ally` (Allied Nation Energy
    Vulnerability Screener). Every data point cites a specific real, public
    source -- see the Scope panel and README.
    """


@energy.command("smr")
@click.argument("installation")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
@click.option("--no-live", is_flag=True, default=False, help="Use cached data only, skip live USGS/GridPulse calls.")
def energy_smr_cmd(installation: str, fmt: str, no_live: bool) -> None:
    """DoD Installation SMR Siting Priority Screen.

    \b
    Example: ir energy smr "Naval Station Newport"
    """
    try:
        result = screen_installation(installation, use_live=not no_live)
    except ValueError as exc:
        energy_dashboard.console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)

    brief_text = generate_smr_brief(result)

    if fmt == "json":
        energy_dashboard.print_json({
            "installation": result.display_name,
            "total_score": result.total_score,
            "tier": result.tier,
            "components": [{"name": c.name, "points": c.points, "max_points": c.max_points, "basis": c.basis} for c in result.components],
            "seismic": {"sdc": result.seismic.sdc, "pga_m": result.seismic.pga_m, "source": result.seismic.source},
            "installation_demand_mwh": result.installation_demand_mwh,
            "brief": brief_text,
        })
        return

    energy_dashboard.print_banner()
    energy_dashboard.print_smr_result(result)
    energy_dashboard.print_brief(brief_text)
    if energy_config.DEMO_MODE:
        energy_dashboard.console.print("[dim]DEMO_MODE=True -- brief uses a deterministic template, not a live Claude call.[/dim]")


@energy.command("eroei")
@click.argument("source")
@click.option("--context", "context_installation", default=None, help="Installation to contextualize against (e.g. 'Naval Station Newport').")
def energy_eroei_cmd(source: str, context_installation: str | None) -> None:
    """Installation EROEI (Energy Return on Energy Invested) lookup.

    \b
    Example: ir energy eroei nuclear --context "Naval Station Newport"
    """
    try:
        result = get_eroei(source, context_installation)
    except ValueError as exc:
        energy_dashboard.console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)

    energy_dashboard.print_banner()
    energy_dashboard.print_eroei_result(result)


@energy.command("eroei-sources")
def energy_eroei_sources_cmd() -> None:
    """List available EROEI source keys."""
    energy_dashboard.print_banner()
    energy_dashboard.console.print("Available sources: " + ", ".join(list_sources()))


@energy.command("ally")
@click.argument("country")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
@click.option("--no-live", is_flag=True, default=False, help="Use cached data only, skip live World Bank calls.")
def energy_ally_cmd(country: str, fmt: str, no_live: bool) -> None:
    """Allied Nation Energy Vulnerability Screener.

    \b
    Example: ir energy ally Japan
    """
    try:
        result = screen_country(country, use_live=not no_live)
    except ValueError as exc:
        energy_dashboard.console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)

    brief_text = generate_ally_brief(result)

    if fmt == "json":
        energy_dashboard.print_json({
            "country": result.country,
            "score": result.score,
            "tier": result.tier,
            "import_dependency_pct": result.import_dependency_pct,
            "import_year": result.import_year,
            "renewable_share_pct": result.renewable_share_pct,
            "renewable_year": result.renewable_year,
            "brief": brief_text,
        })
        return

    energy_dashboard.print_banner()
    energy_dashboard.print_ally_result(result)
    energy_dashboard.print_brief(brief_text)


@energy.command("installations")
def energy_installations_cmd() -> None:
    """List joule's supported installation roster."""
    energy_dashboard.print_banner()
    energy_dashboard.console.rule("[bold]Supported Installations[/bold]")
    for key, inst in energy_config.INSTALLATIONS.items():
        energy_dashboard.console.print(f"  {inst['display_name']}  [dim](key: '{key}')[/dim]")


@energy.command("demo")
def energy_demo_cmd() -> None:
    """Run all three modules against the flagship demo case (Naval Station
    Newport, Japan)."""
    energy_dashboard.print_banner()

    energy_dashboard.console.rule("[bold]Demo 1: SMR Siting Screen -- Naval Station Newport[/bold]")
    smr_result = screen_installation("naval station newport")
    energy_dashboard.print_smr_result(smr_result)
    energy_dashboard.print_brief(generate_smr_brief(smr_result))

    energy_dashboard.console.rule("[bold]Demo 2: EROEI -- Nuclear, contextualized to Naval Station Newport[/bold]")
    eroei_result = get_eroei("nuclear", "naval station newport")
    energy_dashboard.print_eroei_result(eroei_result)

    energy_dashboard.console.rule("[bold]Demo 3: Allied Nation Vulnerability -- Japan[/bold]")
    ally_result = screen_country("Japan")
    energy_dashboard.print_ally_result(ally_result)
    energy_dashboard.print_brief(generate_ally_brief(ally_result))

    energy_dashboard.console.print("[dim]All demo output cites real sources -- see README. DEMO_MODE=True uses deterministic brief templates.[/dim]")


if __name__ == "__main__":
    ir()
