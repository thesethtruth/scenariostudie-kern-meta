#%% packages
import pandas as pd
from pypsa import Network

from helpers import load_costs, open_config_yaml_to_dict
from renamer import DATA_FOLDER

#%% globals
NETWORKS = list(DATA_FOLDER.glob("*.nc"))

fp_config = "config_pypsa.yaml"
config = open_config_yaml_to_dict(fp_config)
country = "NL"
fp_cost = "costs.csv"

## START LOOP
#%%  load in network
nfp = NETWORKS[0]
n = Network(str(nfp))
year = int(nfp.stem[:4])

legacy_gt_to_hydrogen = config["enable"]["legacy_gt_to_hydrogen"]
costs = load_costs(
    fp_cost,
    config["costs"],
    config["electricity"],
    year=year,
    legacy_gt_to_hydrogen=legacy_gt_to_hydrogen,
)

df = pd.Series()

#%% CCS quantity (Mt)
BECCS = n.generators.query("carrier =='BECCS'").copy()
BECCS["country"] = [i[:2] for i in BECCS.index]
BECCS = BECCS.query("country == @country").index

BECCS_MWh = n.generators_t["p"][BECCS].sum().sum()
BECCS_CO2_per_MWh = costs.at["BECCS", "co2_emissions"]
df["negative_emissions_beccs"] = -1 * BECCS_MWh * BECCS_CO2_per_MWh

#%% DAC quantity (Mt)
DAC = n.generators.query("carrier =='DAC'").copy()
DAC["country"] = [i[:2] for i in DAC.index]
DAC = DAC.query("country == @country").index

DAC_MWh = n.generators_t["p"][DAC].sum().sum()
DAC_CO2_per_MWh = costs.at["DAC", "co2_emissions"]
df["negative_emissions_dac"] = -1 * DAC_MWh * DAC_CO2_per_MWh

#%% deployed capacity [MW]
from viewerfunctions import extract_deployed_capacity
from definitions import NICE_NAMES


dep_cap = (
    extract_deployed_capacity(n=n)
    .query("country == @country")
    .groupby("carrier")
    .sum()["p_nom_opt"]
    .rename(NICE_NAMES)
)

df = pd.concat([df, dep_cap])

#%% deployed energy capacity [MWh]
from viewerfunctions import extract_storage_units_deployed_energy

storage_energy = extract_storage_units_deployed_energy(n=n, country=country)[
    "p_nom_opt"
]

df = pd.concat([df, storage_energy])
