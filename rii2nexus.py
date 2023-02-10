"""Convert the refractiveindex.info database to nexus"""
from collections import namedtuple
from functools import lru_cache, partial
import os
from pathlib import Path
import logging
import re
from typing import List
import pandas as pd
import yaml
from ase.data import chemical_symbols
from tqdm import tqdm

from nexusutils.dataconverter.convert import convert, logger

logger.setLevel(logging.ERROR)


def load_rii_database():
    """Loads the rii database"""
    Entry = namedtuple(
        "Entry",
        [
            "category",
            "category_description",
            "material_category",
            "material",
            "material_description",
            "reference",
            "reference_category",
            "reference_description",
            "path",
        ],
    )

    rii_path = Path("refractiveindex.info-database/database")

    yml_file = yaml.load(
        rii_path.joinpath("library.yml").read_text(encoding="utf-8"), yaml.SafeLoader
    )

    entries = []
    for category in yml_file:
        material_div = pd.NA
        for material in category["content"]:
            if "DIVIDER" in material:
                material_div = material["DIVIDER"]
                continue

            ref_div = pd.NA
            for ref in material["content"]:
                if "DIVIDER" in ref:
                    ref_div = ref["DIVIDER"]
                    continue

                entries.append(
                    Entry(
                        category["SHELF"],
                        category["name"],
                        material_div,
                        material["BOOK"],
                        material["name"],
                        ref["PAGE"],
                        ref_div,
                        ref["name"],
                        os.path.join("data", os.path.normpath(ref["data"])),
                    )
                )

    return pd.DataFrame(entries, dtype=pd.StringDtype())


def yml_path2nexus_path(path: str) -> str:
    """Converts the yml path to a nexus path"""
    path, fname = path.replace("data/", "dispersions/").rsplit("/", 1)
    os.makedirs(path, exist_ok=True)
    return Path(path) / f"{fname.rsplit('.', 1)[0]}.nxs"


def prefix_path(path: str) -> str:
    """Adds prefix to the database path"""
    return f"refractiveindex.info-database/database/{path}"


def parse_mat_desc(material_description: str):
    """Parse the material description into a formula and colloquial names"""

    def get_colloq_names():
        colloq_names = []
        if polymer:
            colloq_names.append(f"({formula})n")
        if colloquial_names:
            colloq_names.append(colloquial_names)
        return colloq_names

    def clean_formula():
        return re.sub(r"[^A-Za-z0-9]", "", formula)

    material_description = re.sub(r"\<[^\>]*\>", "", material_description)
    polymer = re.match(r"\(([^\)]+)\)n", material_description)
    if polymer:
        formula = polymer.group(1)
        colloquial_names = material_description.rsplit(")n", 1)[-1].strip("() ")
        return clean_formula(), get_colloq_names()

    mat_descr = re.match(r"^(.*)\(([^\(\)]+)\)$", material_description)
    formula, colloquial_names = (
        mat_descr.groups() if mat_descr else (material_description, "")
    )

    return clean_formula(), get_colloq_names()


@lru_cache(maxsize=None)
def element_regex():
    """Compiles a regex to find element symbols"""
    element_names = chemical_symbols.copy()  # Don't mess with the ase internal list
    element_names.remove("X")
    element_names += ["D", "T"]
    # Sort and reverse to ensure matching longer element names first (i.e. Si before S)
    element_names.sort()
    element_names.reverse()

    return re.compile(rf"({'|'.join(element_names)})(\d*)")


def hill_sorted_elements(elements):
    """Get a Hill sorted list of (element, amount) tuples from an input list"""
    elems_dict = {}
    for elem, amount in elements:
        elems_dict[elem] = elems_dict.get(elem, 0) + (int(amount) if amount else 1)

    elems = []
    if "C" in elems_dict:
        c_amount = elems_dict.pop("C")
        h_amount = elems_dict.pop("H", 0)
        elems += [("C", c_amount)]
        if h_amount:
            elems += [("H", h_amount)]
    elems += sorted(elems_dict.items())

    return elems


def fill(metadata: dict, entry: pd.DataFrame):
    """Fill the data dict from the entry"""
    clean_chemical_formula, colloquial_names = parse_mat_desc(
        entry["material_description"]
    )
    metadata["/ENTRY[entry]/sample/chemical_formula"] = clean_chemical_formula
    if colloquial_names:
        metadata["/ENTRY[entry]/sample/colloquial_name"] = ", ".join(colloquial_names)

    elements = element_regex().findall(clean_chemical_formula)
    if elements:
        elems = hill_sorted_elements(elements)
        metadata["/ENTRY[entry]/sample/atom_types"] = ",".join(list(zip(*elems))[0])

        chemical_formula = ""
        for elem, amount in elems:
            chemical_formula += f"{elem}{amount}" if amount > 1 else f"{elem}"
        metadata["/ENTRY[entry]/sample/chemical_formula"] = chemical_formula

    # TODO: Add model/experimental information
    # and phase information (bulk, solid, liquid)
    # metadata["/ENTRY[entry]/material_phase"]
    #               one of [gas, liquid, solid, other]
    # metadata["/ENTRY[entry]/material_phase_comment"]
    #               additional information if the field above is otherdispersion_type
    # metadata["/ENTRY[entry]/additional_phase_information"]
    #               additional info such as crystaline phase
    # metadata["/ENTRY[entry]/dispersion_type"] =
    #               one of [measured, simulated]


def write_nexus(path: str, metadata: dict):
    """Write a nexus file from the dispersion data"""
    filename = path.split("/", 2)[-1].replace("/", "-")
    convert(
        input_file=[prefix_path(path)],
        objects=[metadata],
        reader="rii_database",
        nxdl="NXdispersive_material",
        output=yml_path2nexus_path(f"{path.rsplit('/', 2)[0]}/{filename}"),
        download_bibtex=True,
    )


def create_nexus(entry, catalog):
    """Create a nexus file from a rii entry"""

    def skip_entries(skip_on: List[str]) -> bool:
        for skip in skip_on:
            if f"-{skip}." in entry["path"]:
                logging.info("Skipping entry: %s", entry["path"])
                return True
        return False

    def get_secondary_entry(base: str, secondary: str) -> pd.DataFrame:
        path = entry["path"].replace(f"-{base}.", f"-{secondary}.")
        sec_entry = catalog[catalog["path"] == path]
        assert len(sec_entry) == 1
        return path

    def fill_uniaxial_entry() -> bool:
        if "-o." in entry["path"]:
            metadata = {}
            logging.info("Searching for e axis for %s", entry["reference"])
            e_path = get_secondary_entry("o", "e")

            metadata = {}
            metadata["dispersion_z"] = prefix_path(e_path)
            fill(metadata, entry)
            write_nexus(entry["path"], metadata)

            return True
        return False

    def fill_biaxial_entry() -> bool:
        if "-alpha." in entry["path"]:
            logging.info("Searching for beta and gamma axis for %s", entry["reference"])
            beta_path = get_secondary_entry("alpha", "beta")
            gamma_path = get_secondary_entry("alpha", "gamma")

            metadata = {}
            metadata["dispersion_y"] = prefix_path(beta_path)
            metadata["dispersion_z"] = prefix_path(gamma_path)
            fill(metadata, entry)
            write_nexus(entry["path"], metadata)

            return True
        return False

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


def create_nexus_database(catalog: pd.DataFrame):
    """Creates the nexus database from the rii database"""
    tqdm.pandas()
    catalog.progress_apply(partial(create_nexus, catalog=catalog), axis=1)


def extract_metadata(catalog: pd.DataFrame, samples=5):
    """Extract metadata from a sample"""

    def fill_n_print(entry):
        print(entry)
        metadata = {}
        metadata["/ENTRY[entry]/literature"] = entry["reference_description"].split(
            ":", 1
        )[0]
        fill(metadata, entry)
        print(metadata)

    catalog.sample(samples).apply(fill_n_print, axis=1)


if __name__ == "__main__":
    database = load_rii_database()

    create_nexus_database(database)
    # extract_metadata(database)
