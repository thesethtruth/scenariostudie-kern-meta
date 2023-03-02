# stringer.py
from itertools import product

scenarios = ["ADAPT", "TRANSFORM"]
years = [2030, 2040, 2050]

for scenario, year in product(scenarios, years):

    target = scenario + str(year)
    print(f'=IF(ISBLANK({target}!AP1); ""; {target}!AP1)')



#%%
for i in range(6):
    print(f'=IF(ISNA(VLOOKUP($M$2;$A$3:$H$60;{3+i};FALSE));"";VLOOKUP($M$2;$A$3:$H$60;{3+i};FALSE))')