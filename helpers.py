import pandas as pd
import yaml
from vresutils.costdata import annuity

idx = pd.IndexSlice

def open_config_yaml_to_dict(fp:str):
    """ convenience function for loading in config.yaml DRY """
    with open(fp, "r") as infile:
        try:
            config = yaml.safe_load(infile)
        except yaml.YAMLError as exc:
            print(exc)
    return config

def load_costs(tech_costs, config, elec_config, year, Nyears=1., legacy_gt_to_hydrogen=[]):

    # set all asset costs and other parameters
    costs = pd.read_csv(tech_costs, index_col=list(range(3))).sort_index()

    # correct units to MW and EUR
    costs.loc[costs.unit.str.contains("/kW"),"value"] *= 1e3
    costs.loc[costs.unit.str.contains("USD"),"value"] *= config['USD2013_to_EUR2013']

    costs = (costs.loc[idx[:,year,:], "value"]
             .unstack(level=2).groupby("technology").sum(min_count=1))
    
    fallback_values = {
        "CO2 intensity" : 0,
        "FOM" : 0,
        "VOM" : 0,
        "discount rate" : config['discountrate'],
        "efficiency" : 1,
        "fuel" : 0,
        "investment" : 0,
        "lifetime" : 25
    }
    
    for parameter, value in fallback_values.items():
        if not parameter in costs.columns:
            costs[parameter] = value

    costs = costs.fillna(fallback_values)

    costs["capital_cost"] = ((annuity(costs["lifetime"], costs["discount rate"]) +
                             costs["FOM"]/100.) *
                             costs["investment"] * Nyears)
    # used for conventional plants
    costs['capital_cost_fixed_only'] = costs["FOM"]/100.*costs["investment"] * Nyears

    costs.at['OCGT', 'fuel'] = costs.at['gas', 'fuel']
    costs.at['CCGT', 'fuel'] = costs.at['gas', 'fuel']

    if legacy_gt_to_hydrogen:
        for gt in legacy_gt_to_hydrogen:
            # try except; also works when costs are assumed from parent technology in _add_missing_carriers_from_costs
            try:
                costs.at[gt, 'fuel'] # raises KeyError if user did not specify costs for this technology
                costs.at[gt, 'fuel'] = 0
            except KeyError:
                pass

    costs['marginal_cost'] = costs['VOM'] + costs['fuel'] / costs['efficiency']

    costs = costs.rename(columns={"CO2 intensity": "co2_emissions"})

    costs.at['OCGT', 'co2_emissions'] = costs.at['gas', 'co2_emissions']
    costs.at['CCGT', 'co2_emissions'] = costs.at['gas', 'co2_emissions']
    
    if legacy_gt_to_hydrogen:
        for gt in legacy_gt_to_hydrogen:
            # try except; also works when costs are assumed from parent technology in _add_missing_carriers_from_costs
            try:
                costs.at[gt, 'co2_emissions'] # raises KeyError if user did not specify costs for this technology
                costs.at[gt, 'co2_emissions'] = 0
            except KeyError:
                pass

    costs.at['solar', 'capital_cost'] = 0.5*(costs.at['solar-rooftop', 'capital_cost'] +
                                             costs.at['solar-utility', 'capital_cost'])

    def costs_for_storage(store, link1, link2=None, max_hours=1.):
        capital_cost = link1['capital_cost'] + max_hours * store['capital_cost']
        if link2 is not None:
            capital_cost += link2['capital_cost']
        return pd.Series(dict(capital_cost=capital_cost,
                              marginal_cost=0.,
                              co2_emissions=0.))

    max_hours = elec_config['max_hours']
    costs.loc["battery"] = \
        costs_for_storage(costs.loc["battery storage"], costs.loc["battery inverter"],
                          max_hours=max_hours['battery'])
    costs.loc["H2"] = \
        costs_for_storage(costs.loc["hydrogen underground storage"], costs.loc["fuel cell"],
                          costs.loc["electrolysis"], max_hours=max_hours['H2'])

    for attr in ('marginal_cost', 'capital_cost'):
        overwrites = config.get(attr)
        if overwrites is not None:
            overwrites = pd.Series(overwrites)
            costs.loc[overwrites.index, attr] = overwrites

    return costs

def reverse(d: dict):
    return {v: k for k,v in d.items()}