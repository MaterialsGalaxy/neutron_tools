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
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")  # needed to "find" GSAS-II modules
# sys.path.append('/home/mkscd/miniconda3/envs/GSASII/bin') # needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore


def run_gsas2_fit(
    project_fn,
    samp_refs,
    inst_refs,
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
    samp_refs: str
        sample parameters to refine
    inst_refs: str
        isntrument parameters to refine
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

    # set initial values
    # for h in gpx.histograms():
    #    h.setHistEntryValue(['Sample Parameters', 'DisplaceX'], 0.001)
    # can also use h.getHistEntryList(keyname='Sample Parameters') to get a list of the values

    #  instrument and sample refinement steps by default will apply to all phases and histograms
    samp_ref_list = samp_refs.split(',')
    """
    samplerefdict = {
        "set": {
            "Sample Parameters": [
                "DisplaceX",
                "DisplaceY",
                "Scale",
                "Absorption"
            ]
        }
    }
    """
    samp_ref_dict = {
        "set": {"Sample Parameters": samp_ref_list},
        "call": HistStats,
    }
    # instrument refinement steps by default will apply to all phases and histograms
    inst_ref_list = inst_refs.split(',')
    inst_ref_dict = {
        "set": {"Instrument Parameters": inst_ref_list},
        "call": HistStats,
    }
    dictList = [samp_ref_dict, inst_ref_dict]
    """
    instrumentrefdict = {
        "set": {
            "Instrument Parameters":[
                'U',
                'V',
                'W',
                'X',
                'Y',
                'Z',
                'SH/L',
                'alpha',
                'beta-0',
                'beta-1',
                'beta-q',
                'sig-0',
                'sig-1',
                'sig-2',
                'sig-q',
                'difA',
                'difB',
                'difC',
                'Zero',
                'SH/L',
                'Polariz.',
                'Lam'
            ]
        }

    }
    """
    # before fit, save project file first. Then in the future, the refined project file will update this one.
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
