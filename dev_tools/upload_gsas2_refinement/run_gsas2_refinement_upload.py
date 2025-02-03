import os
import sys
from typing import (
    Any,
    Dict,
    Union,
)

import numpy as np
import shutil
"""
change how GSASIIscriptable is imported for actual deployment
locally i added:
    conda activate GSASII
in the tool xml commands to get this to work
"""

# import G2script as G2sc
gsas2_scriptable_path = os.path.join(os.environ["CONDA_PREFIX"], "GSAS-II/GSASII")
sys.path.append(gsas2_scriptable_path)
# needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    structure_fns,
    gsa_fns,
    prm_fns,
    output_stem_fn,
    output_gpx,
    output_lst,
    num_cycles=5,
    init_vals: Union[None, Dict[str, Any]] = None,
):
    """
    Parameters
    ----------
    structure_fns:list [str]
        input structure cif filenames
    gsa_fns: list[str]
        input gsa,raw powder data filenames
    prm_fns: list [str]
        input instrument profile filenames
    output_stem_fn: str
        output stem filename.
    ouput_gpx: str
        path of the output GSASII project file
    output_lst: str
        path of the output GSASII refinement lst file
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

    proj_path = os.path.join(os.getcwd(), output_stem_fn + "_initial.gpx")

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
    # add histograms to project
    for i , gsa_fn in enumerate(gsa_fns):
        gpx.add_powder_histogram(gsa_fn, prm_fns[i])


    # step 2: add phases and link it to the all histograms
    for structure_fn in structure_fns:
        gpx.add_phase(
            structure_fn, fmthint="CIF", histograms=gpx.histograms()
        )
    print("phase loaded")

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
    gpx.save(os.path.join(os.getcwd(), output_stem_fn + "_refined.gpx"))

    gpx.do_refinements(dictList)
    print("================")

    # save necessary output files to output directories passed by galaxy
    lst_file_path = os.path.join(os.getcwd(), output_stem_fn + "_refined.lst")
    gpx.save(filename=output_gpx)
    shutil.copy(lst_file_path, output_lst)

    return 0
