import numpy as np
import GSASIIscriptable as G2sc  # type: ignore


def load_phase_constraints(gpx):
    """
    load the phase constraints previously added to the project
    seems to not be readable
    """
    phase_constraint_list = gpx.get_Constraints("Phase")
    return phase_constraint_list


def hist_export(gpx, histogram_name):
    """
    returns histogram data for plotting
    """
    h = gpx.histogram(histogram_name)
    x = np.array(h.getdata("X"))
    y = np.array(h.getdata("Yobs"))
    ycalc = np.array(h.getdata("Ycalc"))
    dy = np.array(h.getdata("Residual"))
    bkg = np.array(h.getdata("Background"))

    return x, y, ycalc, dy, bkg


def load_histogram_parameters(gpx, histogram_name):
    h = gpx.histogram(histogram_name)
    sample_dict = h.getHistEntryValue(["Sample Parameters"])
    inst_dict = h.getHistEntryValue(["Instrument Parameters"])[0]
    sp = {}
    ip = {}
    # initialise parameter dictionaries with fixed keynames
    for param, value in sample_dict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # sp[new_param_name] = value
        sp[param] = value

    for param, value in inst_dict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # ip[new_param_name] = value
        ip[param] = value

    srl = []
    irl = []
    sc = {}
    ic = {}
    inst_noref_list = ["Type", "Bank", "Lam1", "Lam2", "Azimuth", "2-theta", "fltPath"]
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


def gsas_load_gpx(input_gpx_file, fn):
    """loads gpx from input file and saves it to output file
    the current project is in outputfile so the loaded ones
    from the galaxy history remain unchanged"""
    gpx = G2sc.G2Project(gpxfile=input_gpx_file, newgpx=fn)
    gpx.save()
    return gpx
