import os
import sys
import numpy as np

"""
change how GSASIIscriptable is imported for actual deployment
locally i added:
    conda activate GSASII
in the tool xml commands to get this to work
"""
# import G2script as G2sc
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")
# needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    project_fn,
    atom_labels,
    atom_refinements,
    output_stem_fn,
    output_path,
    num_cycles=5,
):
    print(atom_labels, "\n")
    print(atom_refinements, "\n")

    # validate the atom_refinement inputs

    atom_refinements = [s.replace(",", "").strip() for s in atom_refinements]

    print(atom_refinements, "\n")

    """
    Parameters
    ----------
    project_fn: str
        input GSAS .gpx project file name
    atom_labels: list [str]
        input atom labels
    atom_refinements: list [str]
        input atom refinement flags
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

    # create atoms refinement dictionary

    atom_dict = dict(zip(atom_labels, atom_refinements))

    # create refinement dictionary

    refdict = {"set": {'Atoms': atom_dict}}

    # before fit, save project file first.
    # Then in the future, the refined project file will update this one.
    gpx.save(os.path.join(os.getcwd(),
                          "portal/", output_stem_fn + "_refined.gpx"))

    gpx.do_refinements([refdict])
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

    output_cif_fn = os.path.join(os.getcwd(),
                                 "portal/", output_stem_fn + "_refined.cif")
    gpx.phases()[0].export_CIF(output_cif_fn)
    cell_r = gpx.phases()[0].get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
