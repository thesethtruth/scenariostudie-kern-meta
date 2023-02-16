#%% packages
import pandas as pd
from pypsa import Network

from helpers import load_costs, open_config_yaml_to_dict
from renamer import DATA_FOLDER

#%% globals
NETWORKS = list(DATA_FOLDER.glob("*.nc"))

fp_config = "config_pypsa.yaml"
config = open_config_yaml_to_dict(fp_config)

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
BECCS = n.generators.query("carrier =='BECCS'").index
BECCS_MWh = n.generators_t["p"][BECCS].sum().sum()
BECCS_CO2_per_MWh = costs.at["BECCS", "co2_emissions"]
df["negative_emissions_beccs"] = -1 * BECCS_MWh * BECCS_CO2_per_MWh

#%% DAC quantity (Mt)
DAC = n.generators.query("carrier =='DAC'").index
DAC_MWh = n.generators_t["p"][DAC].sum().sum()
DAC_CO2_per_MWh = costs.at["DAC", "co2_emissions"]
df["negative_emissions_dac"] = -1 * DAC_MWh * DAC_CO2_per_MWh

#%%
