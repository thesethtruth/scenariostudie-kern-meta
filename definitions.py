#%%
from pathlib import Path
from helpers import open_config_yaml_to_dict
import pandas as pd
import numpy as np

NWE_BOUNDS = [[-10, 41], [15, 60]]
CONFIG_PATH = Path(__file__).parent / "config_viewer.yaml"
CONFIG = open_config_yaml_to_dict(CONFIG_PATH)
NICE_NAMES = CONFIG["nice_names"]
REGION_NICE_NAMES = CONFIG["region_nice_names"]
TECH_COLORS = CONFIG["tech_colors"]
NETWORK_PATH = Path(__file__).parent / "trial_network"
GTS = ["CCGT-nextgen", "OCGT-nextgen", "OCGT", "CCGT"]
FUELCELL = ["H2 Fuel Cell"]
H2_GENS = [*GTS, *FUELCELL]

LLIM_ONWIND_BE = 3700  # MW

URL_VOYAGER_NOLABEL = (
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
)

ELECTROLYSER = ["H2 Electrolysis"]
MAX_HOURS_STORAGE_UNITS = 6

STAT_COLS_T = ["maximum", "mininum", "average", "total"]


SNAPSHOT_YEAR = {"2040": "2040", "2050": "2050", "2070": "2070"}

DEMAND_SCENARIO = {
    "National": "national",
    "Regional": "regional",
    "European": "european",
    "International": "international",
}

CO2REDUCTION = {"100%": "100.0", "103%": "103.0", "110%": "110.0", "120%": "120.0"}

NUCLEAR_OPTION = {
    "Disabled": "disabled",
    "High [High WACC (7%) EPR]": "centralized_high",
    "Medium [Low WACC (3.8%) EPR]": "centralized_medium",
    "Medium (everywhere)": "centralized_medium+EVERYWHERE",
    "Low [Low WACC (3.8%) AP1000]": "centralized_low",
    "SMR [Low WACC (3.8%) SMR]": "SMR",
    "SMR (everywhere)": "SMR+EVERYWHERE",
    "Fusion (everywhere)": "fusion+EVERYWHERE",
}

LL_WILDCARD = {
    "Unlimited": "copt",
    r"100% of today": "v1.0",
    r"140% of today": "v1.4",
    r"150% of today": "v1.5",
    r"160% of today": "v1.6",
    r"175% of today": "v1.75",
    r"190% of today": "v1.9",
    r"225% of today": "v2.25",
}

ONWIND = {
    "No potential limits": "",
    r"40% of onland wind potential": "onwind+p0.4",
    r"30% of onland wind potential": "onwind+p0.3",
    r"25% of onland wind potential": "onwind+p0.25",
}

EQ = {
    "Geen eisen aan zelfvoorziening": "",
    r"50% van regionale vraag": "EQ0.5",
    r"70% van nationale vraag": "EQ0.7c",
    r"80% van nationale vraag": "EQ0.8c",
    r"90% van nationale vraag": "EQ0.9c",
}

RENEWABLE_LOWER = {
    "Greenfield renewables": "greenfield",
    "eRisk 2030 projection": "eRisk+2030",
    "eRisk 2035 projection": "eRisk+2035",
    "Havenbedrijf Rotterdam": "rotterdam",
}

HYDROGEN_DEMAND = {
    "No hydrogen demand": "",
    "No hydrogen demand": "h2+0.0",
    "Hydrogen demand 100%": "h2+1.0",
    "Hydrogen demand 133%": "h2+1.33",
    "Hydrogen demand 150%": "h2+1.5",
    "Hydrogen demand 225%": "h2+2.25",
    "Hydrogen demand 240%": "h2+2.40",
    "Hydrogen demand 250%": "h2+2.5",
}

DISCOUNT_RATE = {
    r"1.85%": "0.0185",
    r"2.65%": "0.0265",
    r"3.8%": "0.038",
    r"2.25%": "0.0225",
}

SCENARIO_OPTIONS = {
    "Snapshot year": SNAPSHOT_YEAR,
    "Nuclear investment configuration": NUCLEAR_OPTION,
    "Technology deployment potentials": ONWIND,
    "Lower limit of renewables": RENEWABLE_LOWER,
    "Hydrogen demand": HYDROGEN_DEMAND,
    "Zelfvoorziening": EQ,
    "Demand scenario": DEMAND_SCENARIO,
    "CO2 reduction target": CO2REDUCTION,
    "Line expansion limits": LL_WILDCARD,
    "Discount rate": DISCOUNT_RATE,
}

SCENARIO_OPTIONS_MAP = {
    "Snapshot year": "snapshot_year",
    "Demand scenario": "demand_scenario",
    "CO2 reduction target": "co2reduction",
    "Line expansion limits": "ll_wildcard",
    "Nuclear investment configuration": "nuclear_option",
    "Technology deployment potentials": "onwind",
    "Lower limit of renewables": "renewable_lower",
    "Hydrogen demand": "h2_demand",
    "Zelfvoorziening": "energy_selfconsumption",
    "Discount rate": "discount_rate",
}


COUNTRIES = {
    # "Noordwest Europa": "none",
    "Nederland": "NL",
    "Duitsland": "DE",
    "België": "BE",
    "Frankrijk": "FR",
    "Denemarken": "DK",
    "Noorwegen ": "NO",
    "Verenigd Koninkrijk": "GB",
    "Luxemburg": "LU",
}

COUNTRY_NICE_NAMES = {
    #   "DE" : "DE",
    #   "DK" : "DK",
    #   "FR" : "FR",
    #   "BE" : "BE",
    "GB": "VK",
    #   "LU" : "LU",
    #   "NL" : "NL",
    #   "NO" : "NO",
}

COUNTRIES_REVERSE = {v: k for k, v in COUNTRIES.items()}

NICE_NAMES_REVERSE = {v: k for k, v in NICE_NAMES.items()}


class ShapeHolder:
    ATTRS = [
        "countries",
        "offshore",
        "onshore",
    ]

    basepath = "/shapes/"

    def __init__(self):

        for attr in self.ATTRS:
            path = self.basepath + attr + ".geojson"
            setattr(self, attr, path)


SHAPES = ShapeHolder()

TECHNOLOGY_EFFICIENCIES = {
    "2040": {
        "OCGT-nextgen": 0.59,
        "CCGT-nextgen": 0.42,
        "OCGT": 0.59,
        "CCGT": 0.42,
        "electrolysis": 0.75,
        "H2 fuel cell": 0.54,
    },
    "2050": {
        "OCGT-nextgen": 0.6,
        "CCGT-nextgen": 0.44,
        "OCGT": 0.6,
        "CCGT": 0.44,
        "electrolysis": 0.8,
        "H2 fuel cell": 0.57,
    },
}


options_fp = "data/options.csv"
OPTIONS = (
    pd.read_csv(options_fp, index_col=0)
    .reset_index()
    .drop(["index"], axis=1)
    .fillna("")
    .astype(str)
)
try:
    OPTIONS.rename({"reduction": "co2reduction"}, axis=1, inplace=True)
except KeyError:
    pass

OPTIONS["co2reduction"] = OPTIONS["co2reduction"].astype(float).round(1).astype(str)

# ['eRisk', 'greenfield', 'eRisk+2035', 'eRisk+2030']

renwlower2030_path = "data/agg_p_nom_minmax_2030.csv"
renwlower2035_path = "data/agg_p_nom_minmax_2035.csv"
renwlower2030 = pd.read_csv(renwlower2030_path).set_index("carrier", drop=True)
renwlower2030[["min", "max"]] = renwlower2030[["min", "max"]].divide(1e3)
renwlower2035 = pd.read_csv(renwlower2035_path).set_index("carrier", drop=True)
renwlower2035[["min", "max"]] = renwlower2035[["min", "max"]].divide(1e3)
renwlower_other = renwlower2035.copy()
renwlower_other[["min", "max"]] = np.nan

RENEWABLE_LOWER = {
    "eRisk+2030": renwlower2030,
    "eRisk+2035": renwlower2035,
    "greenfield": renwlower_other,
    "rotterdam": renwlower2035,
}


PLOT_COORDINATES = {
    "NL1 4": dict(x=3.717442, y=51.432026),
    "NL1 4 H2": dict(x=3.717442, y=51.432026),
    "BE1 1": dict(x=3.647875, y=50.867598),
    "BE1 1 H2": dict(x=3.647875, y=50.867598),
    "DK1 0": dict(x=9.211402, y=56.383764),
    "DK1 0 H2": dict(x=9.211402, y=56.383764),
    "DK3 0": dict(x=11.796807, y=55.392618),
    "DK3 0 H2": dict(x=11.796807, y=55.392618),
    "NO2 0": dict(x=7.167058, y=58.627846),
    "NO2 0 H2": dict(x=7.167058, y=58.627846),
    "DE1 4": dict(x=8.519820, y=53.140068),
    "DE1 4 H2": dict(x=8.519820, y=53.140068),
}


SVG_CONFIG = {
    "toImageButtonOptions": {
        "format": "svg",  # one of png, svg, jpeg, webp
        "filename": "image",
        "height": 450,
        "width": 900,
        "scale": 1,  # Multiply title/legend/axis/canvas sizes by this factor
    }
}

SVG_CONFIG2 = {
    "toImageButtonOptions": {
        "format": "svg",  # one of png, svg, jpeg, webp
        "filename": "image",
        "height": 350,
        "width": 1600,
        "scale": 1,  # Multiply title/legend/axis/canvas sizes by this factor
    }
}

#%%
# test_all_options
from helpers import reverse
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


columns = {
    SCENARIO_OPTIONS_MAP[key]: reverse(value) for key, value in SCENARIO_OPTIONS.items()
}

missing_opt = False
for col, options in columns.items():

    existing_options = OPTIONS[col].unique()

    for option in existing_options:
        if option not in options.keys():
            logger.warning(
                f"LOG: {__name__}: Option '{option}' [{type(option)}] of category '{col}' is not in the dropdowns!"
            )
            missing_opt = True

if not missing_opt:
    logger.info(
        f"LOG: {__name__}: All options found in {options_fp} are included in the dropdowns"
    )
