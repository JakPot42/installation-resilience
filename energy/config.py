"""config.py — every number here cites a specific real, public document.
No logic lives here. See README "Data sourcing" for the full citation
list and the one real research finding that shaped this design: DoD's
CURRENT-format public energy reporting (the Annual Energy Performance,
Resilience, and Readiness Report, FY2018+) publishes only DoD-wide and
service-level aggregates -- no per-installation breakdown. The last
public per-installation breakdown found was the FY2014 Annual Energy
Management Report, Appendix E. That is the most recent real, citable,
per-installation figure available, and is used here, dated and disclosed
as such rather than silently treated as current.
"""
from __future__ import annotations

from demo_mode import is_demo_mode

DEMO_MODE = is_demo_mode()
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

SCOPE_DISCLAIMER = (
    "Every number in this tool cites a specific real, public document -- DoD "
    "energy reports, USGS/World Bank live APIs, or published vendor/NRC/DOE "
    "specs. Where a figure is dated or a disclosed estimate rather than a "
    "live current value, that is stated explicitly, not hidden. This tool "
    "does not make a siting recommendation or regulatory determination -- "
    "it screens for further engineering/regulatory review."
)

# BTU -> MWh: 1 BTU = 2.930711e-7 MWh (standard conversion; 3,412.142 BTU/kWh).
BBTU_TO_MWH = 293.0711

# Average U.S. nuclear fleet capacity factor -- EIA reports the U.S. nuclear
# fleet has operated above 90% for over a decade (routinely ~92-93%).
# Source: U.S. EIA, "What is U.S. electricity generation by energy source,"
# nuclear capacity factor statistics (eia.gov/tools/faqs).
NUCLEAR_CAPACITY_FACTOR = 0.92

# ---------------------------------------------------------------------------
# SMR designs -- real, published specs. Both are NRC-engaged designs as of
# this build; neither is operating commercially in the U.S. yet.
# ---------------------------------------------------------------------------
SMR_DESIGNS: dict[str, dict] = {
    "nuscale_voygr": {
        "vendor": "NuScale Power",
        "design_name": "VOYGR (uprated 77 MWe module)",
        "module_mwe": 77.0,
        "configurations": {"VOYGR-4": 4, "VOYGR-6": 6, "VOYGR-12": 12},
        "epz_claim": "Site boundary only (no offsite EPZ) -- NuScale's EPZ "
                      "sizing methodology was concurred-with by the NRC's "
                      "Advisory Committee on Reactor Safeguards (ACRS) in "
                      "2022; final EPZ size is still a site-specific NRC "
                      "determination, not a blanket guarantee.",
        "nrc_status": "Original 50 MWe NuScale design NRC-certified 2023 "
                       "(first U.S.-certified SMR design). Uprated 77 MWe "
                       "design approved by the NRC May 30, 2025.",
        "citation": "DOE, 'NRC Approves NuScale Power's Uprated Small "
                     "Modular Reactor Design' (energy.gov/ne/articles); "
                     "NuScale press release, 'NuScale's Emergency Planning "
                     "Zone boundary methodology validated by the NRC "
                     "Advisory Committee on Reactor Safeguards' (2022).",
    },
    "ge_hitachi_bwrx300": {
        "vendor": "GE Vernova Hitachi Nuclear Energy",
        "design_name": "BWRX-300",
        "module_mwe": 300.0,
        "module_mwt": 870.0,
        "configurations": {"single unit": 1},
        "footprint": "Power block 430ft x 200ft (131m x 61m); 6.7-acre "
                      "protected area.",
        "epz_claim": "1,000 m from the site boundary (GEH claim).",
        "nrc_status": "In NRC pre-application review. First unit under "
                       "construction at Darlington, Ontario (non-U.S.) -- "
                       "targeted commercial operation end of 2030.",
        "citation": "GE Vernova, 'BWRX-300 General Description' "
                     "(005N9751 Rev, gevernova.com); GE Vernova BWRX-300 "
                     "product page (nuclear.gepower.com).",
    },
}

# ---------------------------------------------------------------------------
# Installation roster -- real per-installation total-site-energy figures
# from DoD's FY2014 Annual Energy Management Report, Appendix E (the most
# recent public per-installation breakdown; see module docstring). Real
# public installation coordinates (GPS aggregators / MilBases.com, same
# citation class already used for P44's SENSITIVE_FACILITIES). Real 2020
# Decennial Census populations for the nearest population center.
# ---------------------------------------------------------------------------
INSTALLATIONS: dict[str, dict] = {
    "naval station newport": {
        "display_name": "Naval Station Newport, RI",
        "lat": 41.53, "lon": -71.31,
        "location_citation": "Public installation location (MilBases.com, "
                               "GPS coordinate aggregators). Home of the "
                               "Naval War College and the Naval Undersea "
                               "Warfare Center (NUWC) Newport.",
        "fy2014_site_energy_bbtu": 626,
        "fy2014_sqft_thousand": 6350,
        "fy2014_intensity_btu_sf": 98636,
        "energy_citation": "DoD FY2014 Annual Energy Management Report, "
                             "Appendix E-11, 'Navy NAVSTA Newport, Newport, "
                             "Rhode Island' (acq.osd.mil archive).",
        "nearest_population_center": "Newport, RI",
        "nearest_population": 25163,
        "population_citation": "U.S. Census Bureau, 2020 Decennial Census, "
                                 "QuickFacts: Newport city, Rhode Island.",
        "gridpulse_region": "NE",
    },
    "naval submarine base kings bay": {
        "display_name": "Naval Submarine Base Kings Bay, GA",
        "lat": 30.7994, "lon": -81.5115,
        "location_citation": "Public installation location (Commander, Navy "
                               "Region Southeast public site) -- same "
                               "coordinates/citation used in P44 Airspace "
                               "Awareness's facility reference list.",
        "fy2014_site_energy_bbtu": 687,
        "fy2014_sqft_thousand": 5335,
        "fy2014_intensity_btu_sf": 128704,
        "energy_citation": "DoD FY2014 Annual Energy Management Report, "
                             "Appendix E, 'Navy Submarine Base Kings Bay, "
                             "Kings Bay, Georgia' (acq.osd.mil archive).",
        "nearest_population_center": "Kingsland, GA",
        "nearest_population": 18337,
        "population_citation": "U.S. Census Bureau, 2020 Decennial Census, "
                                 "QuickFacts: Kingsland city, Georgia.",
        "gridpulse_region": None,   # Georgia isn't one of GridPulse's 6 covered regions
    },
    "edwards air force base": {
        "display_name": "Edwards Air Force Base, CA",
        "lat": 34.9054, "lon": -117.8837,
        "location_citation": "Public installation location (edwards.af.mil) "
                               "-- same coordinates/citation used in P44 "
                               "Airspace Awareness's facility reference list.",
        "fy2014_site_energy_bbtu": 743,
        "fy2014_sqft_thousand": 6734,
        "fy2014_intensity_btu_sf": 110344,
        "energy_citation": "DoD FY2014 Annual Energy Management Report, "
                             "Appendix E, 'Air Force Edwards Air Force "
                             "Base, Lancaster, California' (acq.osd.mil "
                             "archive).",
        "nearest_population_center": "Lancaster, CA",
        "nearest_population": 173516,
        "population_citation": "U.S. Census Bureau, 2020 Decennial Census, "
                                 "QuickFacts: Lancaster city, California.",
        "gridpulse_region": "CAL",
    },
    "travis air force base": {
        "display_name": "Travis Air Force Base, CA",
        "lat": 38.2627, "lon": -121.9271,
        "location_citation": "Public installation location (travis.af.mil "
                               "/ GPS coordinate aggregators).",
        "fy2014_site_energy_bbtu": 447,
        "fy2014_sqft_thousand": 6234,
        "fy2014_intensity_btu_sf": 71683,
        "energy_citation": "DoD FY2014 Annual Energy Management Report, "
                             "Appendix E, 'Air Force Travis Air Force "
                             "Base, Fairfield, California' (acq.osd.mil "
                             "archive).",
        "nearest_population_center": "Fairfield, CA",
        "nearest_population": 119881,
        "population_citation": "U.S. Census Bureau, 2020 Decennial Census, "
                                 "QuickFacts: Fairfield city, California.",
        "gridpulse_region": "CAL",
    },
}

# ---------------------------------------------------------------------------
# EROEI (Energy Return on Energy Invested) reference table. Point/range
# values from World Nuclear Association's "Energy Return on Investment"
# compilation (world-nuclear.org), which itself aggregates primary peer-
# reviewed studies -- principally Weissbach et al. 2013 ("Energy
# intensities, EROIs, and energy payback times of electricity generating
# power plants," Energy 52) plus Gagnon et al. 2002 for hydro. Solar PV
# figure cross-checked against NREL's own PV EROEI publication.
# Diesel/liquid-fuel generators are deliberately NOT included: DoD
# literature doesn't commonly report an EROEI figure for them (fully
# burdened cost of fuel / logistics-tail metrics are the standard DoD
# framing instead) -- omitted rather than estimated, per the "never
# generate a number that isn't traceable to a real document" rule.
# ---------------------------------------------------------------------------
EROEI_SOURCES: dict[str, dict] = {
    "nuclear": {
        "label": "Nuclear (PWR/BWR, large light-water reactor)",
        "eroi_low": 59, "eroi_high": 75,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment' (world-nuclear.org), Table 2, "
                     "aggregating Weissbach et al. 2013.",
    },
    "smr_nuclear": {
        "label": "SMR (nuclear) -- no dedicated EROEI study found; nuclear "
                  "fuel-cycle EROEI is not strongly module-size-dependent, "
                  "so the large-LWR figure is used as the best available "
                  "proxy, disclosed as such.",
        "eroi_low": 59, "eroi_high": 75,
        "citation": "Same as 'nuclear' above -- proxy value, not a "
                     "SMR-specific study.",
    },
    "natural_gas_ccgt": {
        "label": "Natural gas (combined-cycle gas turbine)",
        "eroi_low": 28, "eroi_high": 28,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment,' Table 2 (CCGT), aggregating Weissbach "
                     "et al. 2013.",
    },
    "coal": {
        "label": "Coal (underground black / open-pit brown)",
        "eroi_low": 29, "eroi_high": 31,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment,' Table 2, aggregating Weissbach et al. 2013.",
    },
    "hydro": {
        "label": "Hydroelectric",
        "eroi_low": 43, "eroi_high": 50,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment,' Table 2; Quebec-specific EROI of 205 "
                     "reported separately (Gagnon et al. 2002).",
    },
    "wind_onshore": {
        "label": "Wind (onshore)",
        "eroi_low": 16, "eroi_high": 35,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment,' Table 2 (Enercon E-66=16, Vestas "
                     "turbine=35.3), aggregating Weissbach et al. 2013.",
    },
    "solar_pv_utility": {
        "label": "Solar PV (utility-scale, moderate insolation)",
        "eroi_low": 3.8, "eroi_high": 12.0,
        "citation": "World Nuclear Association, 'Energy Return on "
                     "Investment,' Table 2 (polycrystalline Si=3.8, "
                     "rooftop=10.6); cross-checked against NREL, 'Energy "
                     "Return on Energy Invested (EROEI) for Photovoltaic "
                     "Solar Systems in Regions of Moderate Insolation' "
                     "(docs.nrel.gov/docs/fy17osti/67901.pdf).",
    },
}

OUTPUT_DIR = "output"
