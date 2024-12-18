import numpy as np
import GSASIIscriptable as G2sc  # type: ignore
from typing import (
    NewType,
)

GSAS2Project = NewType("GSAS2Project", type[G2sc.G2Project])


def load_phase_constraints(gpx: GSAS2Project) -> list:
    """loads a list of phase constraints from a GSASII Project object

    Args:
        gpx (GSAS2Project): GSASII project object containing all data about the project

    Returns:
        list: a list of all the phase constraints in the project. Each constraint is itself a list
        containing the constraint type, parameters, coefficients and refinement flag.
    """
    phase_constraint_list = gpx.get_Constraints("Phase")
    return phase_constraint_list


def hist_export(gpx: GSAS2Project, histogram_name: str) -> tuple:
    """gathers the data required for plotting a histogram from the powder data
    in the GSASII Project under histogram_name

    Args:
        gpx (GSAS2Project): GSASII project object containing all data about the project
        histogram_name (str): name of the selected histogram in the project

    Returns:
        tuple: of numpy arrays of data for plotting: x values, y values, y-fit values,
        residuals and background.
    """
    h = gpx.histogram(histogram_name)
    x = np.array(h.getdata("X"))
    y = np.array(h.getdata("Yobs"))
    ycalc = np.array(h.getdata("Ycalc"))
    dy = np.array(h.getdata("Residual"))
    bkg = np.array(h.getdata("Background"))

    return x, y, ycalc, dy, bkg


def load_histogram_parameters(
    gpx: GSAS2Project, histogram_name: str
) -> tuple[list, dict, dict, list, dict, dict]:
    """gathers instrument and sample parameters data that can be accessed and changed in the app.
    This function makes lists of active refinement flags in the instrument and sample parameter data.
    Also dictionaries of parameters which can be refined are generated too.

    Args:
        gpx (GSAS2Project): GSASII project object containing all data about the project
        histogram_name (str): name of the selected histogram in the project

    Returns:
        tuple[list, dict, dict, list, dict, dict]: [0,1,2] The instrument parameter data, [3,4,5] The sample parameter data
        both sets start with the active refinement list, a parameters dictionary with the current values,
        and a dictionary for the UI of parameters which can be refined.
    """
    h = gpx.histogram(histogram_name)
    sample_dict: dict = h.getHistEntryValue(["Sample Parameters"])
    inst_dict: dict = h.getHistEntryValue(["Instrument Parameters"])[0]
    sp: dict = {}
    ip: dict = {}
    # initialise parameter dictionaries with fixed keynames
    for param, value in sample_dict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # sp[new_param_name] = value
        sp[param] = value

    for param, value in inst_dict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # ip[new_param_name] = value
        ip[param] = value

    srl: list = []
    irl: list = []
    sc: dict = {}
    ic: dict = {}
    inst_noref_list: list[str] = [
        "Type",
        "Bank",
        "Lam1",
        "Lam2",
        "Azimuth",
        "2-theta",
        "fltPath",
    ]
    # populating list of sample refinements that are already active
    for param, val in sp.items():
        # set sample choices dict for UI
        if isinstance(val, list):
            if isinstance(val[1], bool):
                sc[param] = param
                if val[1]:
                    srl.append(param)
    # populating list of refinement flags already active
    for param, val in ip.items():
        if isinstance(val, list) and len(val) == 3:
            # set instrument choices dict for UI
            if param not in inst_noref_list:
                ic[param] = param
                if val[2]:
                    irl.append(param)

    return (irl, ip, ic, srl, sp, sc)


def gsas_load_gpx(input_gpx_file: str, fn: str) -> GSAS2Project:
    """loads a GSASII project from input file and saves it to a new file with name "fn".
    This is so any changes can be compared to the original later.

    Args:
        input_gpx_file (str): file path of the GSASII .gpx file to be loaded
        fn (str): The name of the new file where changes will be saved.

    Returns:
        GSAS2Project: GSASII project object containing all data about the project.
    """

    gpx = G2sc.G2Project(gpxfile=input_gpx_file, newgpx=fn)
    gpx.save()
    return gpx
