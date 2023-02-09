"""Parse references from rii yaml files"""
from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional
import requests


def example_references() -> List[str]:
    """Generate a set of example references"""
    references = []

    references.append(
        "1) H.-J. Hagemann, W. Gudat, and C. Kunz. Optical constants "
        "from the far infrared to the x-ray region: "
        "Mg, Al, Cu, Ag, Au, Bi, C, and Al<sub>2</sub>O<sub>3</sub>, "
        '<a href="https://doi.org/10.1364/JOSA.65.000742">'
        "<i>J. Opt. Soc. Am.</i> <b>65</b>, 742-744 (1975)</a>"
        "<br>2) H.-J. Hagemann, W. Gudat, and C. Kunz. "
        '<a href="https://refractiveindex.info/download/data/1974/Hagemann '
        '1974 - DESY report SR-74-7.pdf">DESY report SR-74/7 (1974)</a>'
    )
    references.append(
        "D. E. Aspnes and A. A. Studna. Dielectric functions and optical "
        "parameters of Si, Ge, GaP, GaAs, GaSb, InP, InAs, and InSb from 1.5 to 6.0 eV, "
        '<a href="https://doi.org/10.1103/PhysRevB.27.985">'
        "<i>Phys. Rev. B</i> <b>27</b>, 985-1009 (1983)</a>"
    )
    references.append(
        "K. F. Hulme et al. Synthetic proustite "
        "(Ag<sub>3</sub>AsS<sub>3</sub>): a new crystal for optical mixing, "
        '<a href="https://doi.org/10.1063/1.1754880">'
        "<i>Appl. Phys. Lett.</i> <b>10</b>, 133-135 (1967)</a>"
    )

    return references


@dataclass
class Citation:
    """A representation for a citation"""

    _raw_str: str = field(repr=False)
    ref_str: str
    url: Optional[str]
    doi: Optional[str]
    bibtex: Optional[str] = None

    @staticmethod
    def parse_citations(reference: str, get_bibtex: bool = False):
        """Parses a reference string into its components"""
        cites = re.split(r"<br\s*\/?\s*>", reference)

        clean_cites = []
        for cite in cites:
            clean_cites.append(Citation(cite, get_bibtex))
        return clean_cites

    def __init__(self, ref_str: str, get_bibtex: bool = False):
        self._raw_str = ref_str
        self.ref_str = re.sub(
            r"\<\/?[^\<\>]*\>",
            "",
            re.search(r"(?:\d\))?\s*(.*)", ref_str).group(1),
        )
        self.get_non_doi_url()
        self.get_doi()

        if get_bibtex:
            self.get_bibtex()

    def get_bibtex(self):
        """Requests the bibtext entry for a given doi"""
        if not self.doi:
            return

        req = requests.get(
            f"https://doi.org/{self.doi}",
            timeout=30,
            headers={"Accept": "application/x-bibtex"},
        )
        if req.status_code == 200:
            self.bibtex = req.text

    def get_non_doi_url(self):
        """Extract urls which are not dois"""
        url = re.search(r"href\=\"([^\"]+)\"", self._raw_str)
        self.url = url.group(1) if url and "doi.org" not in url.group(1) else None

    def get_doi(self):
        """Extracts doi from a reference string"""
        doi_match = re.search(r"\".*doi\.org\/([^\"]+)\"", self._raw_str)
        self.doi = doi_match.group(1) if doi_match else None

    def write_entries(self, template: Dict[str, Any], path: str):
        """Write entries to nexusutils template"""
        reference_identifier = "REFERENCES"
        name = basename = "reference"

        while f"{path}/{reference_identifier}[{name}]/text" in template:
            count = locals().get("count", 0) + 1
            name = f"{basename}{count}"

        base_path = f"{path}/{reference_identifier}[{name}]"
        if self.url:
            template[f"{base_path}/url"] = self.url
        if self.doi:
            template[f"{base_path}/doi"] = self.doi
        if self.bibtex:
            template[f"{base_path}/bibtex"] = self.bibtex

        template[f"{base_path}/text"] = self.ref_str


if __name__ == "__main__":
    ex_refs = example_references()

    templ = {}
    for ex_ref in ex_refs:
        refs = Citation.parse_citations(ex_ref, get_bibtex=False)

        for ref in refs:
            ref.write_entries(templ, "/entry")
        # print(refs)
    print(templ)
