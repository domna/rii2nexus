# %%
import re
from typing import List


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


def parse_reference(reference: str):
    """Parses a reference string into its components"""
    refs = re.split("<br/?>", reference)

    for ref in refs:
        print(re.search(r"(\d\))?\s*(.*)", ref).group(2))


if __name__ == "__main__":
    ex_refs = example_references()

    for ex_ref in ex_refs:
        parse_reference(ex_ref)
