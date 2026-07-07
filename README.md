# Installation Resilience (Phase 6, Cluster 5)

Merger of joule, GridPulse, and Water Security Stress Monitor — physical/
energy/water resilience at a specific defense installation. Architecture-
first session, same discipline as the prior four clusters.

## What these three actually are

All three are genuinely CLI-only (Click + Rich), zero web layer, zero
database — no Render services involved anywhere in this cluster.

**GridPulse and Water Monitor are near-twins by design.** Water Monitor
was explicitly built as "the GridPulse pattern applied to water," and it
shows in the real code: identical file layout, byte-identical
`STRESS_TIERS`, a verbatim-duplicated `score_to_tier()`, the same
`apply_scenario`/`run_scenario`/`run_named_scenario` engine shape, the
same `DEMO_BRIEFS`-keyed-by-region demo pattern. Their domain formulas
stay genuinely distinct: grid stress is a net-load/firm-capacity ratio;
water stress is `0.5*supply_stress + 0.5*USDM-weighted-drought-index`.

**joule is a different shape, and already a consumer of GridPulse.** It's
installation-centric (SMR siting, EROEI, ally screening), not a
region-stress dashboard, and its `gridpulse_bridge.py` already reads
GridPulse's `to_joule_format()` export — deliberate file-based loose
coupling per CLAUDE.md's own "aware of each other" guidance for these two
repos.

## Real conflicts found and resolved

- **`gridpulse/brief.py` had no exception handling at all** around its
  live-mode Claude call, unlike its near-identical twin
  `water_monitor/brief.py`, which already wrapped the same call in
  `try/except -> RuntimeError`. Fixed standalone in `gridpulse`'s own
  repo first (own commit/push, 5 new regression tests, 226/226 passing)
  before this shared library existed.
- **Two genuinely different, both-intentional Claude-failure behaviors**:
  `water_monitor`/`gridpulse` raise loudly (a dedicated `brief` command
  should fail, not silently show the wrong content); `joule` falls back
  to its already-computed deterministic template (a screening command's
  score/tier is the substance, the brief is prose on top). Neither is a
  bug -- `claude_brief.py`'s `on_error` parameter makes the choice
  explicit at the call site instead of leaving it implicit in which
  try/except style a file happened to use.
- **`"CAL"` region-key collision with different real-world referents:**
  GridPulse's `"CAL"` is an EIA electricity balancing region; Water
  Monitor's `"CAL"` is a water/drought region. No shared "region" concept
  is forced — each tool keeps its own roster.
- **A third DEMO_MODE convention**: GridPulse/Water Monitor use
  `not in ("false","0","no")`; joule uses strict `== "True"`. Reconciled
  in `demo_mode.py`, same class of drift found and fixed in every prior
  Phase 6 cluster.

## Proposed shape (approved)

One unified CLI with three subcommand groups mapping 1:1 to the source
tools, domain engines ported unchanged:

```
ir energy  smr|eroei|ally|installations     <- joule
ir grid    dashboard|region|scenario|brief|export   <- gridpulse
ir water   dashboard|region|scenario|brief          <- water_monitor
```

No unifying "region" or "installation" data entity — same "shared
infrastructure, not shared data" discipline as Analyst's Desk and Cleared
Facility Suite. The joule<->GridPulse bridge stays file-based even
in-repo, preserving the documented loose-coupling decision.

**Deliberately not being built as part of this merge:** an
`ir installation <name>` command fusing grid + water stress for one
installation's location. joule already maps installations to GridPulse
regions, but an installation-to-water-region mapping doesn't exist yet —
this would be genuinely new capability, not a port of existing code.
Filed as a future enhancement in `CLAUDE.md`, out of scope here.

## `shared` contents (this repo)

- **`stress_core.py`** — the canonical `STRESS_TIERS`/`score_to_tier()`,
  reconciling the byte-identical duplicate between GridPulse and Water
  Monitor into one definition.
- **`demo_mode.py`** — one `is_demo_mode()` convention, reconciling the
  strict-vs-permissive drift described above.
- **`claude_brief.py`** — one `call_claude()` wrapper with an explicit
  `on_error="raise"|"fallback"` parameter, so both of the cluster's real,
  deliberate failure behaviors are supported without guessing which one
  a given call site needs.

## Status

Step 0 (GridPulse's standalone exception-handling fix), Step 1 (this
shared-core library, 37 tests passing, all mocked -- no real network/API
calls), and Step 2 (domain logic ported onto the shared core in `grid/`,
`water/`, `energy/`; unified `ir` CLI in `cli.py` wiring 14 subcommands
across `ir grid`/`ir water`/`ir energy`) are complete, verified with real
CLI invocations (not just the mocked unit tests) for all three groups.

Step 2 verification caught a real bug pytest couldn't see: Water
Monitor's `DEMO_BRIEFS` seed text used em-dashes that rendered as
mojibake on a real Windows cp1252 console (`water brief`/`water demo`)
-- same class of bug as Cluster 4's. Fixed standalone in water-monitor's
own repo first (own commit/push), then synced into this repo's
`water/seed_data.py`.

Step 3 (distribute the shared core back to the 3 standalone repos as a
consistency pass) hasn't started yet.
