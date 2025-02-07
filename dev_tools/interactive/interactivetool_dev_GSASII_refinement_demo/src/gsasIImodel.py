import numpy as np
import GSASIIscriptable as G2sc  # type: ignore
from typing import (
    NewType,
)

GSAS2Project = NewType("GSAS2Project", type[G2sc.G2Project])


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
