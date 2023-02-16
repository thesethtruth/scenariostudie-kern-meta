# Meta analysis of *Scenario study nuclear energy*

[Scenario study nuclear energy (conclusions and summary) [EN]](https://eriskgroup.com/wp-content/uploads/2022/10/Scenario-study-nuclear-energy-Conclusions-and-Summary.pdf)  
[Scenario study nuclear energy (complete report) [NL]](https://open.overheid.nl/documenten/ronl-46fb6f84d40d2ed22a4db4709e932d03f53b82c2/pdf)


## Target data

1. CO2 emmissions total (Mt)
2. CCS quantity (Mt)
3. DAC quantity (Mt)
4. Installed capacity of all technologies (MW)
5. Installed storage capacity of all technologies (MWh)
6. Import and export capacity (GW)
   1. Hydrogen
   2. Electricity
7. Imported and exported quantity (PJ)
   1. Hydrogen
   2. Electricity
   3. Biomass


## Scenarios in scope of analysis

### 2040
1. Geen kernenergie
2. Grootschalige kernenergie
3. SMR

### 2050
1. Geen kernenergie
2. Grootschalige kernenergie
3. SMR

This means:
1. 8365 # €/MWe (disabled)
2. 4100 # €/MWe (centralized_medium)
3. 2700 # €/MWe (SMR) + SMR_FOM_ratio = 1.333

Other options are:
| snapshot_year | renewable_lower | demand_scenario | reduction | nuclear_option     | ll_wildcard | h2_demand | onwind      | discount_rate |
| ------------- | --------------- | --------------- | --------- | ------------------ | ----------- | --------- | ----------- | ------------- |
| 2040          | eRisk+2035      | national        | 100       | centralized_medium | v1.5        | h2+1.33   | onwind+p0.3 | 0.0225        |
| 2040          | eRisk+2035      | national        | 100       | disabled           | v1.5        | h2+1.33   | onwind+p0.3 | 0.0225        |
| 2040          | eRisk+2035      | national        | 100       | SMR                | v1.5        | h2+1.33   | onwind+p0.3 | 0.0225        |
| 2050          | eRisk+2035      | national        | 103       | centralized_medium | v1.75       | h2+1.5    | onwind+p0.3 | 0.0225        |
| 2050          | eRisk+2035      | national        | 103       | disabled           | v1.75       | h2+1.5    | onwind+p0.3 | 0.0225        |
| 2050          | eRisk+2035      | national        | 103       | SMR                | v1.75       | h2+1.5    | onwind+p0.3 | 0.0225        |

Which yields:
| uuid                                                                |
| ------------------------------------------------------------------- |
| 2040eRisk+2035national100.0centralized_mediumv1.5h2+1.33onwind+p0.3 |
| 2040eRisk+2035national100.0disabledv1.5h2+1.33onwind+p0.3           |
| 2040eRisk+2035national100.0SMRv1.5h2+1.33onwind+p0.3                |
| 2050eRisk+2035national103.0centralized_mediumv1.75h2+1.5onwind+p0.3 |
| 2050eRisk+2035national103.0disabledv1.75h2+1.5onwind+p0.3           |
| 2050eRisk+2035national103.0SMRv1.75h2+1.5onwind+p0.3                |

## Demand scenarios

### Electricity
- **2040**: *'Systeemintegratie wind op zee'* (nationale beleidssturing)
- **2050**: *'Integrale Infrastructuurverkenning 2030 - 2050 (II3050)'* (nationale beleidssturing)

### Hydrogen
*Afry, Agora (2021) No-Regret Hydrogen & IEA, CIEP (2021) Hydrogen in North-Western Europe*  
- **2040**: 133% (op basis van II3050 waterstofvraag op jaarbasis)  
- **2050**: 150% (op basis van II3050 waterstofvraag op jaarbasis)

