#%%
import re
from pathlib import Path

import pandas as pd
from jinja2 import Template
from pretty_html_table import build_table

fp = Path("D:/Users/WIES4/Desktop/Meta-local/Format Taak 1_macro_nieuw.xlsx").resolve()

xl = pd.ExcelFile(fp)

if False:
    for sheet in xl.sheet_names:
        print(sheet)

studies = [
    "TNO_klimaatneutraal",
    "II3050v2",
    "Startanalyse",
    "World_Energy_outlook_IEA",
    "scenariostudie_kernenergie",
    "Routekaart_waterstof",
    "TYNDP2022",
    "KIVI_EnergyNL2050",
    "WimTurkenburg",
    "Urgenda",
    "Elektrificatie_industrie",
    "Systeemintegratie_WOZ",
    "DNV_ETO ",
    "Guidehouse PVI",
]
html_studies = []

#%%

for study in studies:
    df = pd.read_excel(
        fp,
        sheet_name=study,
        skiprows=[0, 1, 2],
        header=0,
        index_col=[0, 1, 2],
        usecols=[0, 1, 2, 3, 4],
        skipfooter=96,
    )
    df.drop(["Datatype - toelichting"], inplace=True, axis=1)

    with open("pretty_table_template.html") as file_:
        template = Template(file_.read())

    (
        study_name,
        study_link,
        date,
        author,
        client,
        study_goal,
        study_focus,
    ) = df.iloc[0:7, 0].values

    df.drop(df.iloc[0:7, 0].index, inplace=True)

    out_df = df.reset_index()
    out_df.columns = ["Categorie", "Subcategorie", "Parameter", "Waarde"]
    out_df = out_df[~out_df["Waarde"].isna()]
    pretty_table = build_table(out_df, "green_light")
    table = pretty_table
    
    ## TODO: add a way to fix the unsuported chars


    try:
        publication_date = f"{date.year}"
    except AttributeError:
        publication_date = date

    html_studies.append(
        template.render(
            study_name=study_name,
            author=author,
            client=client,
            publication_date=publication_date,
            study_goal=study_goal,
            study_focus=study_focus,
            study_link=study_link,
            table=table,
        )
    )

# Save to html file

with open("big_template.html") as file_:
    template = Template(file_.read())

result = template.render(studies=html_studies)
with open("result.html", "w") as f:
    f.write(result)
