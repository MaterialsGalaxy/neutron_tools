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
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")  # needed to "find" GSAS-II modules
# sys.path.append('/home/mkscd/miniconda3/envs/GSASII/bin') # needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    project_fn,
    eqn_var_list,
    eqn_coef_list,
    eqn_tot,
    equiv_var_list,
    equiv_coef_list,
    output_stem_fn,
    output_path,
    num_cycles=5,
):
    print(eqn_var_list, "\n")
    print(eqn_coef_list, "\n")
    print(eqn_tot, "\n")
    print(equiv_var_list, "\n")
    print(equiv_coef_list, "\n")

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

    proj_path = os.path.join(os.getcwd(), "portal/",
                             output_stem_fn + "_initial.gpx")

    print(proj_path)

    # load from input project save to new name and directory
    gpx = G2sc.G2Project(gpxfile=project_fn, newgpx=proj_path)
    gpx.save(proj_path)
    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)


    cell_i = gpx.phases()[0].get_cell()

    # step 3: increase # of cycles to improve convergence
    gpx.data["Controls"]["data"]["max cyc"] = num_cycles

    # add equation constraints

    gpx.add_EqnConstr(eqn_tot, eqn_var_list, multlist=eqn_coef_list)

    # add equivalence constraints

    gpx.add_EquivConstr(equiv_var_list, multlist=equiv_coef_list)

    # before fit, save project file first.
    # Then in the future, the refined project file will update this one.
    gpx.save(os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.gpx"))

    gpx.refine()
    print("================")

    # save results data

    rw = gpx.histogram(0).get_wR() * 0.01
    x = np.array(gpx.histogram(0).getdata("X"))
    y = np.array(gpx.histogram(0).getdata("Yobs"))
    ycalc = np.array(gpx.histogram(0).getdata("Ycalc"))
    dy = np.array(gpx.histogram(0).getdata("Residual"))
    bkg = np.array(gpx.histogram(0).getdata("Background"))

    refs = gpx.histogram(0).reflections()
    ref_list = refs[gpx.phases()[0].name]["RefList"]

    output_cif_fn = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.cif")
    gpx.phases()[0].export_CIF(output_cif_fn)
    cell_r = gpx.phases()[0].get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
