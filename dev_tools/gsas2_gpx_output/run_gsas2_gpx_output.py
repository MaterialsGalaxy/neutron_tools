import os
import sys
import shutil
import numpy as np
from deepdiff import Delta

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
    project_fn,
    output_stem_fn,
    output_path,
):
    """
    Parameters
    ----------
    project_fn: str
        input GSAS .gpx project file name
    output_stem_fn: str
        output stem filename.
    output_path: str
        path to put output files

    Returns
    -------

    """

    print("INFO: Build GSAS-II Project File.")
    print("******************************")

    # start GSAS-II refinement
    # create a project file

    proj_path = os.path.join(os.getcwd(), output_stem_fn + "_refined.gpx")

    print(proj_path)

    # load from input project save to new name and directory
    gpx = G2sc.G2Project(gpxfile=project_fn)

    gpx.save(filename=proj_path)
    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)

    # generate output CIF files

    for phase in gpx.phases():

        output_cif_fn = os.path.join(os.getcwd(),
                                    "portal/",phase.name +"_refined.cif")
        phase.export_CIF(output_cif_fn)
    

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

   
    cell_r = gpx.phases()[0].get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_r, ref_list
