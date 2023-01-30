"""Convert the refractiveindex.info database to nexus"""
import os
from pathlib import Path
import logging
from typing import List
import pandas as pd

from elli.database import RII
from nexusutils.dataconverter.convert import convert

logging.basicConfig(level=logging.WARNING)
database = RII()
database.rii_path = Path("refractiveindexinfo-database/database")


def yml_path2nexus_path(path: str) -> str:
    """Converts the yml path to a nexus path"""
    path, fname = path.replace("data/", "dispersions/").rsplit("/", 1)
    os.makedirs(path, exist_ok=True)
    return Path(path) / f"{fname.rsplit('.', 1)[0]}.nxs"


def prefix_path(path: str) -> str:
    """Adds prefix to the database path"""
    return f"refractiveindex.info-database/database/{path}"


def fill(metadata: dict, entry: pd.DataFrame):
    """Fill the data dict from the entry"""
    metadata["/ENTRY[entry]/chemical_formula"] = entry["book"]
    metadata["/ENTRY[entry]/dispersion_type"] = "measured"


def write_nexus(path: str, metadata: dict):
    """Write a nexus file from the dispersion data"""
    convert(
        input_file=[prefix_path(path)],
        objects=[metadata],
        reader="rii_database",
        nxdl="NXdispersive_material",
        output=yml_path2nexus_path(path),
    )


def create_nexus(entry):
    """Create a nexus file from a rii entry"""

    def skip_entries(skip_on: List[str]) -> bool:
        for skip in skip_on:
            if f"-{skip}." in entry["path"]:
                logging.info("Skipping entry: %s", entry["path"])
                return True
        return False

    def get_secondary_entry(base: str, secondary: str) -> pd.DataFrame:
        path = entry["path"].replace(f"-{base}.", f"-{secondary}.")
        sec_entry = database.catalog[database.catalog["path"] == path]
        assert len(sec_entry) == 1
        return path

    def fill_uniaxial_entry() -> bool:
        if "-o." in entry["path"]:
            metadata = {}
            logging.info("Searching for e axis for %s", entry["page"])
            e_path = get_secondary_entry("o", "e")

            metadata = {}
            metadata["dispersion_z"] = prefix_path(e_path)
            fill(metadata, entry)
            write_nexus(entry["path"], metadata)

            return True
        return False

    def fill_biaxial_entry() -> bool:
        if "-alpha." in entry["path"]:
            logging.info("Searching for beta and gamma axis for %s", entry["page"])
            beta_path = get_secondary_entry("alpha", "beta")
            gamma_path = get_secondary_entry("alpha", "gamma")

            metadata = {}
            metadata["dispersion_y"] = prefix_path(beta_path)
            metadata["dispersion_z"] = prefix_path(gamma_path)
            fill(metadata, entry)
            write_nexus(entry["path"], metadata)

            return True
        return True

    def fill_entry():
        metadata = {}
        fill(metadata, entry)
        write_nexus(entry["path"], metadata)

    if skip_entries(["e", "beta", "gamma"]):
        return

    if fill_uniaxial_entry():
        return

    if fill_biaxial_entry():
        return

    fill_entry()


print(database.catalog.columns.values)
database.catalog.apply(create_nexus, axis=1)
