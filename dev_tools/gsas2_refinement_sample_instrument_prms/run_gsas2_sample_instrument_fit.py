import os
import sys

# from typing import Union, Dict, Any
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
    hist_type,
    samp_refs,
    inst_refs,
    inst_params,
    inst_vals,
    samp_params,
    samp_vals,
    output_stem_fn,
    output_path,
    num_cycles=5,
    # init_vals: Union[None, Dict[str, Any]] = None,
):
    """
    Parameters
    ----------
    project_fn: str
        GSASII gpx project filename
    hist_type: str
        GSASII histogram type
    samp_refs: str
        comma separated sample parameters to refine
    inst_refs: str
        comma separated instrument parameters to refine
    inst_params: list [str]
        instrument parameter key names for setting values.
    inst_vals: list [float]
        instrument parameter values to set
    samp_params: list [float]
        sample parameter key names for setting values.
    samp_vals: list [float]
        sample parameter values to set
    output_stem_fn: str
        output stem filename.
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
    # create a new project file for refinement
    proj_path = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_initial.gpx")

    print(proj_path)

    if os.path.exists(proj_path):
        os.remove(proj_path)

    # load from input project save to new name and directory
    gpx = G2sc.G2Project(gpxfile=project_fn, newgpx=proj_path)
    gpx.save(proj_path)
    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)

    # add six bank histograms to the project
    # hists = []

    cell_i = gpx.phases()[0].get_cell()

    # step 1: increase # of cycles to improve convergence
    gpx.data["Controls"]["data"]["max cyc"] = num_cycles
    """
    setting the instrument and sample parameter values is split into steps.
    step 1: get the previous values in a dictionary
    step 2: change only the selected parameters in the dictionary
    step 3 : set the dictionary values back into the project histogram.
    """

    # get the histogram (for a single powder data file the id is 0)
    h = gpx.histograms()[0]
    # new way of setting
    print(h.getHistEntryValue(["Sample Parameters"]), "\n")
    samp_dict = dict(zip(samp_params, samp_vals))
    samp_dict_full = h.getHistEntryValue(["Sample Parameters"])

    for param in samp_dict:
        if samp_dict[param] != 0.0:  # check for unset parameters
            samp_dict_full[param][0] = samp_dict[param]

    h.setHistEntryValue(["Sample Parameters"], samp_dict_full)

    print(h.getHistEntryValue(["Sample Parameters"]), "\n")

    # new way of setting instrument parameters
    print(h.getHistEntryValue(["Instrument Parameters"])[0], "\n")

    inst_dict = dict(zip(inst_params, inst_vals))
    inst_dict_full = h.getHistEntryValue(["Instrument Parameters"])

    for param in inst_dict:
        if inst_dict[param] != 0.0:  # check for unset parameters
            inst_dict_full[0][param][1] = inst_dict[param]

    h.setHistEntryValue(["Instrument Parameters"], inst_dict_full)

    print(h.getHistEntryValue(["Instrument Parameters"])[0], "\n")

    # sample refinement steps by default will apply
    # to all phases and histograms
    samp_ref_list = samp_refs.split(",")
    samp_ref_dict = {
        "set": {"Sample Parameters": samp_ref_list},
        "call": HistStats,
    }

    # instrument refinement steps by default will apply
    # to all phases and histograms
    inst_ref_list = inst_refs.split(",")
    inst_ref_dict = {
        "set": {"Instrument Parameters": inst_ref_list},
        "call": HistStats,
    }

    dictList = [samp_ref_dict, inst_ref_dict]

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
    ref_list = refs[gpx.phases()[0].name]["RefList"]

    output_cif_fn = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.cif")
    gpx.phases()[0].export_CIF(output_cif_fn)
    cell_r = gpx.phases()[0].get_cell()

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
