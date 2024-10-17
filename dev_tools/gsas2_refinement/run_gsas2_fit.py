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
import GSASIIscriptable as G2sc


def run_gsas2_fit(
    structure_fn,
    gsa_fn,
    prm_fn,
    output_stem_fn,
    stype,
    bank,
    xmin,
    xmax,
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

    # check if the project got created
    if os.path.exists(proj_path):
        print("created project at path:", proj_path)
    else:
        print("no project created at path", proj_path)
    """
    Here the project does get created even though the output prints the second statement
    something is wrong with the output paths in general
    """

    # add six bank histograms to the project
    hists = []

    """
    Galaxy changes all the input files into .dat files through the <inputs> in the tool xml
    fix this by reading them in, and saving the encoded text back to the filetypes that GSAS requires.
    Then pass the path of the new files to the GSAS functions.
    """

    # convert prm file from dat back to prm
    with open(prm_fn, "r") as file:
        content = file.read()
        prm_fn_fixed = open("new_param_file.prm", "w")
        prm_fn_fixed.write(content)
        prm_path = os.path.abspath("new_param_file.prm")
        # print(content)
        prm_fn_fixed.close()

    # convert data file back to raw
    with open(gsa_fn, "r") as file:
        content = file.read()
        gsa_fn_fixed = open("new_pwdr_file.raw", "w")
        gsa_fn_fixed.write(content)
        gsa_path = os.path.abspath("new_pwdr_file.raw")
        # print(content)
        gsa_fn_fixed.close()

    # convert dat file back to CIF
    with open(structure_fn, "r") as file:
        content = file.read()
        cif_fn_fixed = open("new_cif_file.cif", "w")
        cif_fn_fixed.write(content)
        cif_path = os.path.abspath("new_cif_file.cif")
        # print(content)
        cif_fn_fixed.close()

    if stype == "N":
        print("heee!!!")
        # debugging print statements
        print(prm_path)
        print(gsa_path)
        print(cif_path)
        print(bank)
        # prmFile = "pdfitc/utils/NOMAD_2019B_Si_sixbanks_Shifter_instrument_file.prm"
        hist1 = gpx.add_powder_histogram("new_pwdr_file.raw", "new_param_file.prm", databank=bank, instbank=bank)
        print("now!")
        hist1.set_refinements({"Limits": [xmin, xmax]})
    if stype == "X":
        print("here! x-ray!!")
        # prmFile = "pdfitc/utils/PDFNSLSII.instprm"
        hist1 = gpx.add_powder_histogram("new_pwdr_file.raw", "new_param_file.prm")
        hist1.set_refinements({"Limits": [xmin, xmax]})

    hists.append(hist1)

    # step 2: add a phase and link it to the previous histograms
    _ = gpx.add_phase("new_cif_file.cif", phasename="structure", fmthint="CIF", histograms=hists)
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
            "set": {"Background": {"type": bkg_type, "no. coeffs": num_coeffs, "coeffs": coeffs, "refine": True}},
            "call": HistStats,
        }
    else:
        refdict2 = {
            "set": {"Background": {"type": "chebyschev", "no. coeffs": 6, "refine": True}},
            "call": HistStats,
        }
    # refinement step 3: refine lattice parameter and Uiso refinement (Phase)
    refdict3 = {
        "set": {"Atoms": {"all": "U"}, "Cell": True},  # set the Uiso and lattice parameters to be refined
        "call": HistStats,
    }

    dictList = [refdict1, refdict2, refdict3]

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
    ref_list = refs["structure"]["RefList"]

    # output_cif_fn = os.path.join(os.getcwd(), 'data/bragg_gsasii/', output_stem_fn + "_refined.cif")
    output_cif_fn = os.path.join(os.getcwd(), "portal/", output_stem_fn + "_refined.cif")
    gpx.phase("structure").export_CIF(output_cif_fn)
    cell_r = gpx.phase("structure").get_cell()

    # header = "Rw = {} \nx           ycalc           y           dy           bkg".format(rw)
    # np.savetxt(f"{output_stem_fn}bank{str(bank)}.dat",
    #            np.transpose([x, ycalc, y, dy, bkg]),
    #            fmt = '%f', delimiter=' ', header = header)
    # df = pd.DataFrame(
    #     {"rw": rw, "x": x, "y": y, "ycalc": ycalc, "dy": dy, "bkg": bkg})
    # df.update(cell)

    return rw, x, y, ycalc, dy, bkg, cell_i, cell_r, ref_list
