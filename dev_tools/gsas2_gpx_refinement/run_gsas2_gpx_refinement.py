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
gsas2_scriptable_path = os.path.join(os.environ["CONDA_PREFIX"], "GSAS-II/GSASII")
sys.path.append(gsas2_scriptable_path)
# needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    project_fn,
    delta_fns,
    output_stem_fn,
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
    output_gpx: str
        path for the output GSASII project file
    output_lst: str
        path for the output GSASII list file
    output_parameters: str
        path for the output GSASII parameters updated file
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
    # create a readable text file detailing parameter changes
    flat_dicts = total_delta.to_flat_dicts()
    updated_parameters_fp = os.path.join(os.getcwd(), "portal/", "parameters_updated.txt")
    with open(updated_parameters_fp, "w") as updated_parameters_file:
        for change in flat_dicts:
            updated_parameters_file.write(change['action'] + ": " + str(change["path"]) + " = " + str(change["value"]) + "\n")

    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)

    # step 3: increase # of cycles to improve convergence
    gpx.data["Controls"]["data"]["max cyc"] = num_cycles

    # before fit, save project file first.
    # Then in the future, the refined project file will update this one.
    gpx.save(os.path.join(os.getcwd(), output_stem_fn + "_refined.gpx"))
    gpx.do_refinements([{}])

    print("================")

    # output files without dataset collection
    gpx.save(filename=output_gpx)
    lst_file_path = os.path.join(os.getcwd(), output_stem_fn + "_refined.lst")
    shutil.copy(lst_file_path, output_lst)
    shutil.copy(updated_parameters_fp, output_parameters)

    return 0
