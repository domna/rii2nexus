"""Convert the refractiveindex.info database to nexus"""
from pathlib import Path
import logging
from typing import List
import elli
import pandas as pd

logging.basicConfig(level=logging.WARNING)
database = elli.db.RII()
database.rii_path = Path("refractiveindexinfo-database/database")


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
        return sec_entry

    def fill_uniaxial_entry():
        if "-o." in entry["path"]:
            logging.info("Searching for e axis for %s", entry["page"])
            e_entry = get_secondary_entry("o", "e")
            return True
        return False

    def fill_biaxial_entry():
        if "-alpha." in entry["path"]:
            logging.info("Searching for beta and gamma axis for %s", entry["page"])
            beta_entry = get_secondary_entry("alpha", "beta")
            gamma_entry = get_secondary_entry("alpha", "gamma")
            return True
        return True

    def fill_entry():
        pass

    if skip_entries(["e", "beta", "gamma"]):
        return

    if fill_uniaxial_entry():
        return

    if fill_biaxial_entry():
        return

    fill_entry()


database.catalog.apply(create_nexus, axis=1)
