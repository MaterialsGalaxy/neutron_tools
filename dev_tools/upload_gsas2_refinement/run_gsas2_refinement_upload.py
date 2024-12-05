import os
import sys
from typing import (
    Any,
    Dict,
    Union,
)

import numpy as np

"""
change how GSASIIscriptable is imported for actual deployment
locally i added:
    conda activate GSASII
in the tool xml commands to get this to work
"""

# import G2script as G2sc
sys.path.append("/home/dxp41838/miniconda3/envs/GSASII/GSAS-II/GSASII")
# needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    structure_fn,
    gsa_fn,
    prm_fn,
    output_stem_fn,
    stype,
    bank,
    output_path,
    num_cycles=5,
    init_vals: Union[None, Dict[str, Any]] = None,
):
    """
    Parameters
    ----------
    structure_fn: str
        input structure cif filename.
    gsa_fn: str
        input gsa filename.
    prm_fn: str
        input instrument profile filename.
    output_stem_fn: str
        output stem filename.
    stype: str
        scattering type
    banks: str
        bank 1-6.
    xmin: float
        minimum x value
    xmax: float
        maximum x value
    output_path: str
        path to put output files
    num_cycles: int
        number of refinement cycles
    init_vals: dict
        initial input values for refinement

    Returns
    -------
    gsas2_poj : str
        gsas2 .gpx project file
    """

    def HistStats(gpx):
        """prints profile rfactors for all histograms"""
        print("*** profile Rwp, " + os.path.split(gpx.filename)[1])
        for hist in gpx.histograms():
            print("\t{:20s}: {:.2f}".format(hist.name, hist.get_wR()))
        print("")

    print("INFO: Build GSAS-II Project File.")
    print("******************************")

    # start GSAS-II refinement
    # create a project file

    proj_path = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_initial.gpx")

    print(proj_path)

    if os.path.exists(proj_path):
        os.remove(proj_path)
    gpx = G2sc.G2Project(newgpx=proj_path)
    gpx.save()
    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)

    # add six bank histograms to the project
    hists = []
    if stype == "N":
        print("heee!!!")
        # debugging print statements
        print(bank)
        hist1 = gpx.add_powder_histogram(gsa_fn, prm_fn, databank=bank, instbank=bank)
        print("now!")
    if stype == "X":
        print("here! x-ray!!")
        # prmFile = "pdfitc/utils/PDFNSLSII.instprm"
        hist1 = gpx.add_powder_histogram(gsa_fn, prm_fn)

    hists.append(hist1)

    # step 2: add a phase and link it to the previous histograms
    _ = gpx.add_phase(
        structure_fn, phasename="structure", fmthint="CIF", histograms=hists
    )
    print("phase loaded")
    cell_i = gpx.phase("structure").get_cell()

    # step 3: increase # of cycles to improve convergence
    gpx.data["Controls"]["data"]["max cyc"] = num_cycles

    # step 4: start refinement
    # refinement step 1: turn on  Histogram Scale factor
    refdict1 = {
        "set": {"Sample Parameters": ["Scale"]},
        "call": HistStats,
    }
    # refinement step 2: turn on background refinement (Hist)
    if init_vals and "bkg" in init_vals:
        bkg_type = init_vals["bkg"]["Type"]
        num_coeffs = init_vals["bkg"]["NumCoeffs"]
        coeffs = init_vals["bkg"]["Coeffs"]
        refdict2 = {
            "set": {
                "Background": {
                    "type": bkg_type,
                    "no. coeffs": num_coeffs,
                    "coeffs": coeffs,
                    "refine": True,
                }
            },
            "call": HistStats,
        }
    else:
        refdict2 = {
            "set": {
                "Background": {"type": "chebyschev", "no. coeffs": 6, "refine": True}
            },
            "call": HistStats,
        }
    # refinement step 3: refine lattice parameter and Uiso refinement (Phase)
    refdict3 = {
        "set": {"Cell": True},
        "call": HistStats,
    }

    dictList = [refdict1, refdict2, refdict3]

    # before fit, save project file first.
    # Then in the future, the refined project file will update this one.
    gpx.save(os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.gpx"))

    gpx.do_refinements(dictList)
    print("================")

    # save results data

    rw = gpx.histogram(0).get_wR() * 0.01
    x = np.array(gpx.histogram(0).getdata("X"))
    y = np.array(gpx.histogram(0).getdata("Yobs"))
    ycalc = np.array(gpx.histogram(0).getdata("Ycalc"))
    dy = np.array(gpx.histogram(0).getdata("Residual"))
    bkg = np.array(gpx.histogram(0).getdata("Background"))

    refs = gpx.histogram(0).reflections()
    ref_list = refs["structure"]["RefList"]

    output_cif_fn = os.path.join(
        os.getcwd(), "portal/", output_stem_fn + "_refined.cif"
    )
    gpx.phase("structure").export_CIF(output_cif_fn)
    cell_r = gpx.phase("structure").get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
