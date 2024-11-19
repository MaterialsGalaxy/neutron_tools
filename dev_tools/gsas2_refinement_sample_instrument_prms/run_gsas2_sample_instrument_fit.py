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
    inst_vals,
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
        sample parameters to refine
    inst_refs: str
        isntrument parameters to refine
    inst_vals: list [float]
        instrument parameter values to set
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

    # set instrument and sample values
    # get the histogram (for a single powder data file the id is 0)
    h = gpx.histograms()[0]

    # get the sample parameters we want to change and their values
    sampleparams = {
        "Scale": h.getHistEntryValue(["Sample Parameters", "Scale"]),
        "DisplaceX": h.getHistEntryValue(["Sample Parameters", "DisplaceX"]),
        "DisplaceY": h.getHistEntryValue(["Sample Parameters", "DisplaceY"]),
        "Absorption": h.getHistEntryValue(["Sample Parameters", "Absorption"]),
    }
    print(samp_vals, "\n", inst_vals, "\n")
    # set the values in a dictionary
    i = 0
    for param in sampleparams:
        if samp_vals[i] != 0.0:
            sampleparams[param][0] = samp_vals[i]
        i += 1

    print(h.getHistEntryValue(["Instrument Parameters"]), "\n")
    # set the sample parameters in the project file.
    for param in sampleparams:
        h.setHistEntryValue(["Sample Parameters", param], sampleparams[param])
    print(h.getHistEntryValue(["Sample Parameters"]), "\n")

    # get the instrument parameters dictionary
    instdict = h.getHistEntryValue(["Instrument Parameters"])[0]

    if hist_type == "PNC":
        instparams = {
            "Lam": instdict["Lam"],
            "Zero": instdict["Zero"],
            "U": instdict["U"],
            "V": instdict["V"],
            "W": instdict["W"],
            "X": instdict["X"],
            "Y": instdict["Y"],
            "Z": instdict["Z"],
            # "SH/L": instdict['SH/L'],
        }
        # $2_theta $fltPath $Azimuth $difA $difB $difC $beta_0 $beta_1 $beta_q $sig_0 $sig_1 $sig_2 $sig_q $X $Y $Z $Zerot $alpha
    elif hist_type == "PNT":
        instparams = {
            "2-theta": instdict["2-theta"],
            "fltPath": instdict["fltPath"],
            "Azimuth": instdict["Azimuth"],
            "difA": instdict["difA"],
            "difB": instdict["difB"],
            "difC": instdict["difC"],
            "beta-0": instdict["beta-0"],
            "beta-1": instdict["beta-1"],
            "beta-q": instdict["beta-q"],
            "sig-0": instdict["sig-0"],
            "sig-1": instdict["sig-1"],
            "sig-q": instdict["sig-q"],
            "X": instdict["X"],
            "Y": instdict["Y"],
            # "Z": instdict["Z"],
            "Zero": instdict["Zero"],
            "alpha": instdict["alpha"],
        }
    else:
        raise ValueError('Expected histogram type PNT or PNC got "', hist_type, '" instead')
    i = 0
    for param in instparams:
        if inst_vals[i] != 0.0:
            instparams[param][1] = inst_vals[i]
        i += 1

    print(h.getHistEntryValue(["Instrument Parameters"])[0], "\n")
    # set the instrument parameters in the project file
    instdictfull = h.getHistEntryValue(["Instrument Parameters"])
    for param in instparams:
        instdictfull[0][param] = instparams[param]
    h.setHistEntryValue(["Instrument Parameters"], instdictfull)

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
