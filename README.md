# Installation Resilience

**Installation Resilience is a command-line tool for assessing the energy and water resilience of a defense installation.** It brings together three analyses under one CLI: installation energy and small-modular-reactor siting, regional electric-grid stress, and regional water stress.

## What it does

Three subcommand groups, one per analysis:

- **`ir energy`** — screens a military installation for small-modular-reactor (SMR) siting suitability, computes energy return on investment (EROEI) for an energy mix, and assesses an allied nation's energy vulnerability. Every figure cites a specific public source.
- **`ir grid`** — fuses electricity demand and generation-mix data with weather forecasts into an hourly grid-stress index for a region, with what-if scenarios for wind, solar, and demand shocks.
- **`ir water`** — combines streamflow percentiles and drought severity into a regional water-stress score, with what-if scenarios.

The energy tool already knows about the grid tool: an installation in a high grid-stress region scores higher as a candidate for on-site generation, because the surrounding grid can absorb less disruption.

## How it works

Every score and tier is computed deterministically from public data (USGS, EIA, NOAA, the U.S. Drought Monitor, World Bank, and DoD energy reports); the AI only narrates the already-computed numbers into a brief. Demo mode works with no API key.

## Usage

```bash
pip install -r requirements.txt
python cli.py energy smr "Naval Station Newport"
python cli.py grid dashboard
python cli.py water dashboard
```

## About

Installation Resilience combines three independently-built command-line tools — joule (installation energy), GridPulse (grid stress), and the Water Security Stress Monitor — into one unified CLI over a shared core. All three remain fully runnable on their own. This is part of a portfolio of national-security and defense-compliance software.
