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


#%% exported and imported energy (export is positive!)
from typing import Tuple

# BUS0
# p0 (export is positive; The power (p0,q0) at bus0 of a branch is positive if the branch is withdrawing power from bus0, i.e. bus0 is injecting into branch)
# BUS1
# p1 (export is positive; Similarly the power (p1,q1) at bus1 of a branch is positive if the branch is withdrawing power from bus1, negative if the branch is injecting into bus1)
def determine_export_import(
    n: Network, component: str, carrier: str, carrier_buses: pd.Index
) -> Tuple[float, float]:

    component_df = getattr(n, component)

    bus0_in_country = component_df.query(
        "carrier == @carrier"
        + " and (bus0 in @carrier_buses and not bus1 in @carrier_buses)"
    ).index

    bus1_in_country = component_df.query(
        "carrier == @carrier"
        + " and (bus1 in @carrier_buses and not bus0 in @carrier_buses)"
    ).index

    timeseries = getattr(n, f"{component}_t")

    df = timeseries["p0"][bus0_in_country]
    carrier_export = df[df > 0].sum().sum()
    carrier_import = -df[df < 0].sum().sum()

    df = timeseries["p1"][bus1_in_country]

    carrier_export += df[df > 0].sum().sum()
    carrier_import -= df[df < 0].sum().sum()

    return carrier_export, carrier_import


## hydrogen
(df["Export - Waterstof"], df["Import - Waterstof"]) = determine_export_import(
    n=n, component="links", carrier="H2 pipeline", carrier_buses=h2_buses
)


#%% electricity

## DC links
(df["Export - Elektriciteit"], df["Import - Elektriciteit"]) = determine_export_import(
    n=n, component="links", carrier="DC", carrier_buses=ac_buses
)
## AC lines
(ac_export, ac_import) = determine_export_import(
    n=n, component="lines", carrier="AC", carrier_buses=ac_buses
)
df["Export - Elektriciteit"] += ac_export
df["Import - Elektriciteit"] += ac_import
