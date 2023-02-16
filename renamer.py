from pathlib import Path
from shutil import copy2

DATA_FOLDER = Path(r"D:\Users\WIES4\Desktop\Meta\Kernenergie\data").resolve()


for folder in DATA_FOLDER.glob("*"):
    stem = folder.stem

    for file in folder.glob("*.nc"):

        copy2(file, DATA_FOLDER / (stem + file.name))
