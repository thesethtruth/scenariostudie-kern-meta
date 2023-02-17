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
h2_buses = n.buses.query("country == @country and carrier == 'H2'").index
ac_buses = n.buses.query("country == @country and carrier == 'AC'").index

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
df["Negatieve emissies - BECCS"] = -1 * BECCS_MWh * BECCS_CO2_per_MWh

#%% DAC quantity (Mt)
DAC = n.generators.query("carrier =='DAC'").copy()
DAC["country"] = [i[:2] for i in DAC.index]
DAC = DAC.query("country == @country").index

DAC_MWh = n.generators_t["p"][DAC].sum().sum()
DAC_CO2_per_MWh = costs.at["DAC", "co2_emissions"]
df["Negatieve emissies - DAC"] = -1 * DAC_MWh * DAC_CO2_per_MWh

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

dep_cap.index = ["Opgesteld vermogen - " + i for i in dep_cap.index]

df = pd.concat([df, dep_cap])

#%% deployed energy capacity [MWh]
from viewerfunctions import extract_storage_units_deployed_energy

storage_energy = extract_storage_units_deployed_energy(n=n, country=country)[
    "p_nom_opt"
]
storage_energy["Waterstofopslag"] = (
    n.stores[["bus", "e_nom_opt"]].copy().query("bus in @h2_buses")["e_nom_opt"].sum()
)
storage_energy.index = [
    "Opgestelde energiecapaciteit - " + i for i in storage_energy.index
]


df = pd.concat([df, storage_energy])

#%% export capacities

## hydrogen
df["Export/import capaciteit - Waterstof pijpleiding"] = n.links.query(
    "carrier == 'H2 pipeline'"
    + "and ((bus0 in @h2_buses and not bus1 in @h2_buses)"
    + "or (bus1 in @h2_buses and not bus0 in @h2_buses))"
)["p_nom_opt"].sum()

## Links
df["Export/import capaciteit - DC links"] = n.links.query(
    "carrier == 'DC'"
    + "and ((bus0 in @ac_buses and not bus1 in @ac_buses)"
    + "or (bus1 in @ac_buses and not bus0 in @ac_buses))"
)["p_nom_opt"].sum()

## AC
df["Export/import capaciteit - AC overland"] = n.lines.query(
    "(bus0 in @ac_buses and not bus1 in @ac_buses)"
    + "or (bus1 in @ac_buses and not bus0 in @ac_buses)"
)["s_nom_opt"].sum()


#%% exported energy

## hydrogen
# (n.links_t['p0'] - n.links_t['p1'])/n.links_t['p0']

bus0_in_country = n.links.query(
    "carrier == 'H2 pipeline'" + "and (bus0 in @h2_buses and not bus1 in @h2_buses)"
).index

bus1_in_country = n.links.query(
    "carrier == 'H2 pipeline'" + "and (bus0 in @h2_buses and not bus1 in @h2_buses)"
).index

# BUS0
# -1 * p0


# BUS1
# -1 * p1


#%% electricity
