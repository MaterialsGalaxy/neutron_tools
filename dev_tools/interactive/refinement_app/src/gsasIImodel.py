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
