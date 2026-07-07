"""Rich terminal dashboard — ASCII-safe (box.ASCII2) for Windows cp1252
console compatibility, same convention as every other CLI in this
portfolio."""
from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import config

console = Console(width=115)

_BANNER = "[bold cyan]joule -- DoD Energy Resilience Intelligence Tool[/bold cyan]  [dim]v1.0[/dim]"


def print_banner() -> None:
    console.print()
    console.print(_BANNER)
    console.print(Panel(config.SCOPE_DISCLAIMER, box=box.ASCII2, border_style="yellow", title="[bold yellow]Scope[/bold yellow]"))


def print_smr_result(r) -> None:
    console.rule(f"[bold]{r.display_name}[/bold] -- SMR Siting Priority Score")
    t = Table(box=box.ASCII2)
    t.add_column("Component", overflow="fold")
    t.add_column("Points", justify="right")
    t.add_column("Basis", overflow="fold")
    for c in r.components:
        t.add_row(c.name, f"{c.points}/{c.max_points}", c.basis)
    console.print(t)
    console.print(f"[bold]TOTAL: {r.total_score}/100 -- {r.tier}[/bold]")
    if r.grid_context is None:
        console.print("[dim]Regional grid resilience value EXCLUDED (state not in GridPulse's 6 covered regions) -- score rescaled, not penalized.[/dim]")

    console.rule("[bold]SMR Module Output vs. Installation Demand[/bold]")
    t2 = Table(box=box.ASCII2)
    t2.add_column("Design")
    t2.add_column("Configuration")
    t2.add_column("MWe", justify="right")
    t2.add_column("MWh/yr", justify="right")
    t2.add_column("x demand", justify="right")
    for f in r.module_fits:
        t2.add_row(f.vendor, f.configuration, f"{f.total_mwe:.0f}", f"{f.annual_output_mwh:,.0f}", f"{f.output_to_demand_ratio:.1f}x")
    console.print(t2)


def print_eroei_result(r) -> None:
    console.rule(f"[bold]EROEI -- {r.label}[/bold]")
    console.print(f"EROI: {r.eroi_low}-{r.eroi_high}")
    console.print(f"[dim]{r.citation}[/dim]")
    if r.installation_context:
        console.print()
        console.print(r.installation_context)


def print_ally_result(r) -> None:
    console.rule(f"[bold]Allied Nation Energy Vulnerability -- {r.country}[/bold]")
    t = Table(box=box.ASCII2)
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_column("Year", justify="right")
    t.add_column("Source", overflow="fold")
    t.add_row("Energy import dependency", f"{r.import_dependency_pct:.1f}%", str(r.import_year), r.import_source)
    t.add_row("Renewable energy share", f"{r.renewable_share_pct:.1f}%", str(r.renewable_year), r.renewable_source)
    console.print(t)
    console.print(f"[bold]VULNERABILITY SCORE: {r.score}/100 -- {r.tier}[/bold]")


def print_brief(text: str) -> None:
    console.rule("[bold]Brief[/bold]")
    console.print(text)
    console.print()


def print_json(data) -> None:
    import json
    console.print_json(json.dumps(data, default=str))
