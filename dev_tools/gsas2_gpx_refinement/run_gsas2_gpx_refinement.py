import os
import sys
import shutil
import numpy as np
from deepdiff import Delta, DeepDiff

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
    delta_fns,
    output_stem_fn,
    output_path,
    output_gpx,
    output_lst,
    output_parameters,
    num_cycles=5,
):
    """
    Parameters
    ----------
    project_fn: str
        input GSAS .gpx project file name
    delta_fns: list str
        input delta files from deepdiff containing updates for GSASII project object
    output_stem_fn: str
        output stem filename.
    output_path: str
        path to put output files
    num_cycles: int
        number of refinement cycles

    Returns
    -------
    gsas2_poj : str
        gsas2 .gpx project file
    """

    print("INFO: Build GSAS-II Project File.")
    print("******************************")

    # start GSAS-II refinement
    # create a project file

    proj_path = os.path.join(os.getcwd(), output_stem_fn + "_initial.gpx")

    print(proj_path)

    # load from input project save to new name and directory
    og_gpx = G2sc.G2Project(gpxfile=project_fn)
    gpx = og_gpx
    # apply deltas and save the new project.
    for delta_fn in delta_fns:
        delta = Delta(delta_path=delta_fn, safe_to_import={'GSASIIobj.G2VarObj', 'numpy.core.multiarray.scalar', 'numpy.dtype', 'numpy.float64'})
        gpx = gpx + delta
        gpx.save(filename=proj_path)

    # create the total delta as the differnce between the latest and original project
    total_diff = DeepDiff(og_gpx, gpx, exclude_paths="filename")
    total_delta = Delta(total_diff)
    # get the gpx history id from the label of the first included delta file
    gpx_hid = delta_fns[0].split("_")[2]
    # create a readable text file detailing parameter changes
    flat_dicts = total_delta.to_flat_dicts()
    updated_parameters_fp = os.path.join(os.getcwd(), "portal/", "parameters_updated_on_"+gpx_hid+".txt")
    with open(updated_parameters_fp, "w") as updated_parameters_file:
        for change in flat_dicts:
            updated_parameters_file.write(change['action'] + ": " + str(change["path"]) + " = " + str(change["value"]) + "\n")

    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)

    cell_i = gpx.phases()[0].get_cell()

    # step 3: increase # of cycles to improve convergence
    gpx.data["Controls"]["data"]["max cyc"] = num_cycles


    # before fit, save project file first.
    # Then in the future, the refined project file will update this one.
    gpx.save(os.path.join(os.getcwd(), output_stem_fn + "_refined.gpx"))

    gpx.do_refinements([{}])
    print("================")
    gpx_output_file_path = os.path.join(os.getcwd(),"portal/", output_stem_fn + "_refined.gpx")
    gpx.save(filename=gpx_output_file_path)

    lst_file_path = os.path.join(os.getcwd(), output_stem_fn + "_refined.lst")
    lst_output_file_path = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.lst")
    shutil.copy(lst_file_path, lst_output_file_path)
    # save results data

    # output files without dataset collection
    shutil.copy(gpx_output_file_path, output_gpx)
    shutil.copy(lst_file_path, output_lst)
    shutil.copy(updated_parameters_fp, output_parameters)

    rw = gpx.histogram(0).get_wR() * 0.01
    x = np.array(gpx.histogram(0).getdata("X"))
    y = np.array(gpx.histogram(0).getdata("Yobs"))
    ycalc = np.array(gpx.histogram(0).getdata("Ycalc"))
    dy = np.array(gpx.histogram(0).getdata("Residual"))
    bkg = np.array(gpx.histogram(0).getdata("Background"))

    refs = gpx.histogram(0).reflections()
    ref_list = refs[gpx.phases()[0].name]["RefList"]

    """output_cif_fn = os.path.join(os.getcwd(),
                                 "portal/", output_stem_fn + "_refined.cif")
    gpx.phases()[0].export_CIF(output_cif_fn)
    """
    cell_r = gpx.phases()[0].get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
