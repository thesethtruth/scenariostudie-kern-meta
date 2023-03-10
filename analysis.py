#%% packages
import pandas as pd
import numpy as np
from pypsa import Network
from typing import Tuple

from helpers import load_costs, open_config_yaml_to_dict
from renamer import DATA_FOLDER
from viewerfunctions import (
    extract_deployed_capacity,
    extract_storage_units_deployed_energy,
    extract_total_energy_generation_demand,
)

from definitions import NICE_NAMES

#%% globals
NETWORKS = list(DATA_FOLDER.glob("*.nc"))

fp_config = "config_pypsa.yaml"
config = open_config_yaml_to_dict(fp_config)
country = "NL"
fp_cost = "costs.csv"
mf = pd.read_excel(
    "230223cleanformat.xlsx",
    header=[0, 1, 2, 3],
)

## because pandas does a BS autosort if you directly use `index_cols` on read_excel, we use manual assignment of indices
for i in range(4):
    mf.set_index(mf.columns[0], append=True, inplace=True)
mf = mf.droplevel(0, axis=0)
mf.index.names = [*[None] * len(mf.index.names)]

## START LOOP
#%%  load in network
for nfp in NETWORKS:
    n = Network(str(nfp))
    year = int(nfp.stem[:4])
    scenario = nfp.stem.split("_")[2]
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

    #%% energy generation and demand (MWh)

    generation, demand = extract_total_energy_generation_demand(n=n)
    demand = (
        demand.query("country == @country")
        .set_index("technology")
        .drop(["level", "country"], axis=1)
    ).iloc[:, 0]
    generation = (
        generation.query("country == @country")
        .set_index("technology")
        .rename(NICE_NAMES)
        .drop(["level", "country"], axis=1)
    ).iloc[:, 0]

    generation.index = [
        f"Opgewekte energie per technologie - {i}" for i in generation.index
    ]
    demand.index = [f"Energievraag per drager - {i}" for i in demand.index]

    df = pd.concat([df, generation, demand])


    #%% export capacities

    ## hydrogen
    df["Export/import capaciteit - Waterstof pijpleiding"] = n.links.query(
        "carrier == 'H2 pipeline'"
        + "and ((bus0 in @h2_buses and not bus1 in @h2_buses)"
        + "or (bus1 in @h2_buses and not bus0 in @h2_buses))"
    )["p_nom_opt"].sum()

    ## Links
    df["Export/import capaciteit - DC links + AC overland"] = n.links.query(
        "carrier == 'DC'"
        + "and ((bus0 in @ac_buses and not bus1 in @ac_buses)"
        + "or (bus1 in @ac_buses and not bus0 in @ac_buses))"
    )["p_nom_opt"].sum()

    ## AC
    df["Export/import capaciteit - DC links + AC overland"] += n.lines.query(
        "(bus0 in @ac_buses and not bus1 in @ac_buses)"
        + "or (bus1 in @ac_buses and not bus0 in @ac_buses)"
    )["s_nom_opt"].sum()


    #%% exported and imported energy (export is positive!)

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


    #%% map the correct units from MW, MWh and tonnes
    df.index.name = "parameter"
    fdf = df.to_frame(name="result").groupby("parameter").sum()  # sum legacy and nextgen
    units = (
        pd.read_csv("units_required.csv")
        .drop_duplicates(subset=["parameter"])
        .set_index("parameter")
    )

    units.index.name = "parameter"
    fdf = fdf.join(units, how="left", on="parameter")

    unit_map = {
        "PJ": 3.6e-06,
        "GW": 1e-3,
        "Mt": 1e-6,
        "PJ - H2 LHV": 3.6e-06 * costs.at["electrolysis", "efficiency"],
    }
    fdf["result"] = fdf.apply(lambda row: row.result * unit_map[row.unit], axis=1)

    #%% Final cleanup

    fdf = fdf.groupby(["key_indicator", "sector", "categorie", "drager"], dropna=False).sum(
        numeric_only=True
    ) # sum categories with overlap

    fdf.index.names = [*[None] * len(fdf.index.names)]

    fdf = fdf[[not all([pd.isna(x) for x in i]) for i in fdf.index]] # drop rules with no assignment in format


    SCENARIO_MAP = {
        "disabled": "Geen kernenergie",
        "centralized": "Grootschalig kernenergie",
        "SMR": "SMR",
    }
    fdf.columns = pd.MultiIndex.from_arrays(np.array([
        "Scenariostudie ernenergie",
        SCENARIO_MAP[scenario],
        str(year),
        "Nederland"
    ]).reshape(-1, 1))


    #%% insert the results in the format
    for i in fdf.index:
        if not (i in mf.index):
            raise KeyError("Niet gevonden mapping:", i, f"({nfp.stem})")

    mf = pd.concat([mf, fdf], axis=1, sort=False)


mf.to_excel("output.xlsx")