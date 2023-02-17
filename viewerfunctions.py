import re
from typing import List, Tuple
import definitions as defs

import pandas as pd
from pypsa import Network

from definitions import (
    COUNTRIES,
    LLIM_ONWIND_BE,
    MAX_HOURS_STORAGE_UNITS,
    NICE_NAMES,
    PLOT_COORDINATES,
    SCENARIO_OPTIONS,
    SCENARIO_OPTIONS_MAP,
    TECH_COLORS,
    TECHNOLOGY_EFFICIENCIES,
)
from helpers import reverse


def extract_gasturbines_deployed_capacity(n: Network, country: str, snapshot_year: str):
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    def apply_efficiencies(row):
        technology, ext_capacity, opt_capacity = str(row.name), row.p_nom, row.p_nom_opt
        efficiency = TECHNOLOGY_EFFICIENCIES.get(snapshot_year)[technology]
        return (opt_capacity * efficiency, ext_capacity * efficiency)

    df = n.links.query("carrier in @defs.GTS").copy()
    df.carrier = df.carrier.replace({"OCGT-nextgen": "OCGT", "CCGT-nextgen": "CCGT"})
    df["country"] = [i[:2] for i in df.index]
    cdf = (
        df.query("country in @countries")
        .groupby("carrier")[["p_nom_opt", "p_nom"]]
        .sum()
        .apply(apply_efficiencies, axis=1, result_type="broadcast")
        .reindex(df.carrier.unique())
        .sort_index()
        .rename(NICE_NAMES)
    )

    return cdf


def extract_fuel_cells_deployed_capacity(n: Network, country: str, snapshot_year: str):
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    def apply_efficiencies(row):
        technology, ext_capacity, opt_capacity = str(row.name), row.p_nom, row.p_nom_opt
        efficiency = TECHNOLOGY_EFFICIENCIES.get(snapshot_year)[technology]
        return (opt_capacity * efficiency, ext_capacity * efficiency)

    df = n.links.query("carrier in @defs.FUELCELL").copy()
    df["country"] = [i[:2] for i in df.index]
    cdf = (
        df.query("country in @countries")
        .groupby("carrier")[["p_nom_opt", "p_nom"]]
        .sum()
        .apply(apply_efficiencies, axis=1, result_type="broadcast")
        .reindex(df.carrier.unique())
        .sort_index()
        .rename(NICE_NAMES)
    )

    return cdf


def extract_storage_units_deployed_capacity(n: Network, country: str, tech: str = None):
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    df = n.storage_units

    if tech:
        techs = [tech]
    else:
        techs = df.carrier.unique()

    df["country"] = [i[:2] for i in df.index]
    cdf = (
        df.query("country in @countries")
        .query("carrier in @techs")
        .groupby("carrier")[["p_nom", "p_nom_opt"]]
        .sum()
        .reindex(df.carrier.unique())
        .sort_index()
        .rename(NICE_NAMES)
    )

    return cdf


def extract_storage_units_deployed_energy(n: Network, country: str):
    """takes in the deployed capacity and multiplies by the storage duration"""
    return (
        extract_storage_units_deployed_capacity(n=n, country=country)
        .drop([NICE_NAMES["hydro"]])
        .multiply(MAX_HOURS_STORAGE_UNITS)
    )


def extract_electrolyser_energy_demand(n: Network, country: str) -> pd.DataFrame:
    """TWh :: determine the generation per county per HYDROGEN techonlogy"""
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    df = n.links_t.p0.sum(axis=0).to_frame()  # Bus 0 is electric
    df["country"] = [i[:2] for i in df.index]
    df["technology"] = [re.sub("\w{3}\s\d\s", "", i) for i in df.index]

    return (
        df.query("technology == @defs.ELECTROLYSER")
        .query("country in @countries")
        .groupby(["country", "technology"])
        .sum()
        .rename(NICE_NAMES)
    )


def extract_hydro_generation(n: Network, country: str, techs="hydro") -> pd.DataFrame:
    """TWh :: determine the hydro power generation per county"""
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    if techs == "hydro":
        techs = [techs]

    df = n.storage_units_t.p.sum(axis=0).to_frame()

    df["country"] = [i[:2] for i in df.index]
    df["technology"] = [i.split(" ")[-1] for i in df.index]

    return (
        df.query("technology in @techs")
        .query("country in @countries")
        .groupby(["country", "technology"])
        .sum()
        .rename({0: "total"}, axis=1)
        # .rename(NICE_NAMES)
    )


def extract_electricity_generation_from_hydrogen(
    n: Network, country: str
) -> pd.DataFrame:
    """TWh :: determine the generation per county per HYDROGEN techonlogy"""
    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    df = n.links_t.p1.sum(axis=0).to_frame()  # Bus 1 is electric
    df["country"] = [i[:2] for i in df.index]
    df["technology"] = [re.sub("\w{3}\s\d\s", "", i) for i in df.index]

    return (
        df.query("technology in @defs.H2_GENS")
        .query("country in @countries")
        .groupby(["country", "technology"])
        .sum()
        .multiply(
            -1
        )  # negative link is positive generation        # .rename(NICE_NAMES)
    )


def extract_generation_per_country_per_tech(n: Network, country: str) -> pd.DataFrame:
    """TWh :: determine the generation per county per techonlogy"""

    df = n.generators_t.p.sum(axis=0).to_frame()
    df["country"] = [i[:2] for i in df.index]
    df["technology"] = [i.split(" ")[-1] for i in df.index]

    if country:
        countries = [country]
    else:
        countries = COUNTRIES.values()

    return (
        df.query("country in @countries")
        .groupby(["country", "technology"])
        .sum()  # .rename(NICE_NAMES)
    )


def extract_deployed_capacity(n: Network) -> pd.DataFrame:
    """GW :: determine deployed capacity, including H2: electrolyzers and OCGT/CCGT"""

    df_bus = n.buses[["x", "y", "country"]].copy()
    df_gen = n.generators[["bus", "carrier", "p_nom", "p_nom_opt"]].copy()
    df_links = n.links[["bus0", "bus1", "carrier", "p_nom", "p_nom_opt"]].copy()
    df_links = df_links.loc[
        df_links.carrier.isin(
            ["H2 electrolysis", "CCGT", "CCGT-nextgen", "OCGT", "OCGT-nextgen"]
        )
    ]
    df_storage = n.storage_units[["bus", "carrier", "p_nom", "p_nom_opt"]].copy()
    # df_storage = df_storage.loc[df_storage.carrier.isin(['hydro'])]

    H2gen = [
        "H2 electrolysis"
    ]  # exclude H2 bus locations to prevent doubling of coordinate positions
    df_links["bus"] = df_links.loc[df_links.carrier.isin(H2gen)].bus0
    H2use = ["CCGT", "CCGT-nextgen", "OCGT", "OCGT-nextgen"]
    mask_H2use = df_links.carrier.isin(H2use)
    df_links_H2use = df_links[mask_H2use]
    df_links.loc[mask_H2use, "bus"] = df_links_H2use["bus1"]
    df_links = df_links.drop(columns=["bus0", "bus1"])

    df = pd.concat([df_gen, df_links, df_storage])

    df = df.join(df_bus[["x", "y"]], on="bus", how="left").set_index("bus")

    df["country"] = [i[:2] for i in df.index]

    return df


def determine_options(options: pd.DataFrame, this_id: str, all_ids: dict) -> List[dict]:
    nice_name = reverse(SCENARIO_OPTIONS_MAP)[this_id]
    this_options_dropdown = SCENARIO_OPTIONS[nice_name]
    _ = all_ids.pop(this_id)
    other_ids = all_ids

    remaining_options = options
    for key, value in other_ids.items():
        if value is not None:
            remaining_options = remaining_options.query(f"{key} == '{value}'")

    remaining_options_dropdown = [
        {"label": label, "value": value}
        for label, value in this_options_dropdown.items()
        if value in remaining_options[this_id].unique()
    ]
    return remaining_options_dropdown


def rgb_to_hex(r, g, b):
    return "#%02x%02x%02x" % (r, g, b)


def get_colors_from_nicenames_tech(technology):
    nicenames_inverse = {y: x for x, y in NICE_NAMES.items()}
    not_nice_technames = [
        nicenames_inverse.get(nicename, nicename) for nicename in technology
    ]

    colors_generation = [
        TECH_COLORS.get(tech, [0, 0, 0]) for tech in not_nice_technames
    ]
    colors_generation = [
        rgb_to_hex(*color) if isinstance(color, list) else color
        for color in colors_generation
    ]
    return colors_generation


def moveCoordinates(old_buses: pd.DataFrame, new_coordinates: dict = PLOT_COORDINATES):
    df_bus = old_buses.copy()
    for bus, coordinates in new_coordinates.items():
        if bus in df_bus.index:
            df_bus.loc[bus, "x"] = coordinates["x"]
            df_bus.loc[bus, "y"] = coordinates["y"]
        # else:
    #         print(f'Bus {bus} does not exist in input DataFrame')
    # print('geoplot coordinates changed!')
    return df_bus


def update_renewable_lower(
    onwind_factor, renewable_lower, snapshot_year, selected_scenario
):

    lower_limit = LLIM_ONWIND_BE / 1e3

    if onwind_factor < 0.3 and snapshot_year != "2070":
        print(
            f"Onwind factor is {onwind_factor}, setting lower limit onwind to {lower_limit} for BE"
        )
        renewable_lower.loc[
            (renewable_lower.index == "onwind") & (renewable_lower.country == "BE"),
            "min",
        ] = lower_limit

    if "disabled" in selected_scenario:
        renewable_lower.loc[
            (renewable_lower.index == "nuclear_nextgen"),
            "min",
        ] = None

    return renewable_lower


def extract_total_energy_generation_demand(
    n: Network,
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    countries = [col[:2] for col in n.loads_t.p_set.columns]
    mindex = pd.MultiIndex.from_arrays(
        [countries, n.loads_t.p_set.columns], names=["country", "region"]
    )

    df = n.loads_t.p_set.copy()
    df.columns = mindex

    # laad data in
    electric_demand = (
        df.T.groupby(["country"])
        .sum()
        .sum(axis=1)
        .to_frame()
        .rename({0: "total"}, axis=1)
    )
    electric_demand["technology"] = "Elektrische vraag"
    electric_demand.set_index("technology", inplace=True, append=True)

    electrolyser_demand = extract_electrolyser_energy_demand(n, None)
    electrolyser_demand["technology"] = "Waterstofproductie e. vraag"
    electrolyser_demand.set_index("technology", inplace=True, append=True)

    conventional_generation = extract_generation_per_country_per_tech(n, None)
    hydrogen_generation = extract_electricity_generation_from_hydrogen(n, None)
    hydropower_generation = extract_hydro_generation(n, None)

    # categoriseer data in demand en generatie
    df_demand = pd.concat([electric_demand, electrolyser_demand], axis=0)

    df_generation = pd.concat(
        [hydrogen_generation, hydropower_generation, conventional_generation], axis=0
    )

    df_generation = df_generation.rename(
        {
            "offwind-ac": "offwind",
            "offwind-dc": "offwind",
            "nuclear_nextgen": "nuclear",
            "OCGT-nextgen": "OCGT",
            "CCGT-nextgen": "CCGT",
        }
    )

    df_demand = df_demand.stack().reset_index()
    df_generation = df_generation.stack().reset_index()

    df_demand.columns = ["country", "technology", "level", "total"]
    df_generation.columns = ["country", "technology", "level", "total"]

    return df_generation, df_demand
