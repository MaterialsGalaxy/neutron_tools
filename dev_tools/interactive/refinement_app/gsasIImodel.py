import sys
# import os
import numpy as np
sys.path.append("/srv/shiny-server/GSASII")
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")
import GSASIIscriptable as G2sc  # type: ignore


def load_phase_constraints(gpx):
    """
    load the phase constraints previously added to the project
    seems to not be readable
    """
    phase_constraint_list = gpx.get_Constraints('Phase')
    return phase_constraint_list


def hist_export(gpx, histname):
    """
    returns histogram data for plotting
    """
    h = gpx.histogram(histname)
    x = np.array(h.getdata("X"))
    y = np.array(h.getdata("Yobs"))
    ycalc = np.array(h.getdata("Ycalc"))
    dy = np.array(h.getdata("Residual"))
    bkg = np.array(h.getdata("Background"))

    return x, y, ycalc, dy, bkg
    # for i, h in enumerate(gpx.histograms()):
    # hfil = os.path.splitext(gpx_file)[0]+'_'+str(i)  # file to write
    # print('\t', h.name, hfil+'.csv')
    # h.Export(hfil, '.csv')


def load_histogram_parameters(gpx, histname):
    h = gpx.histogram(histname)
    sampledict = h.getHistEntryValue(['Sample Parameters'])
    instdict = h.getHistEntryValue(['Instrument Parameters'])[0]
    sp = {}
    ip = {}
    # initialise parameter dictionaries with fixed keynames
    for param, value in sampledict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # sp[new_param_name] = value
        sp[param] = value

    for param, value in instdict.items():
        # new_param_name = param.translate({ord(i): None for i in './'})
        # ip[new_param_name] = value
        ip[param] = value

    srl = []
    irl = []
    sc = {}
    ic = {}
    inst_noref_list = ["Type", "Bank", "Lam1", "Lam2",
                       "Azimuth", "2-theta", "fltPath"]
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


"""
def load_histogram_parameters(gpx, histname):

    loads a subset of sample and isntrument parameters and refinement
    flags of interest for the UI. Could be extended to everything.

    h = gpx.histogram(histname)

    # Change to full dictionaries
    # add returning of choices dictionary for refinement flags

    # dictionary of subset of sample parameters values of interest
    sampleparams = {
        "Scale": h.getHistEntryValue(['Sample Parameters', 'Scale']),
        "DisplaceX": h.getHistEntryValue(['Sample Parameters', 'DisplaceX']),
        "DisplaceY": h.getHistEntryValue(['Sample Parameters', 'DisplaceY']),
        "Absorption": h.getHistEntryValue(['Sample Parameters', 'Absorption']),
    }
    sp = h.getHistEntryValue(['Sample Parameters'])
    ip = h.getHistEntryValue(['Instrument Parameters'])[0]
    srl = []
    irl = []
    sc = {}
    ic = {}
    # populating list of sample refinements that are already active
    for param, val in sp.items():
        # set sample choices dict for UI
        if isinstance(val[1], bool):
            sc[param] = param
            if val[1] is True:
                srl.append(param)

    # debugging print statements
    print(h.getHistEntryValue(['Instrument Parameters'])[0]['Lam'])
    print(h.getHistEntryValue(['Instrument Parameters']))

    # full instrument parameter dictionary
    # instparams = h.getHistEntryValue(['Instrument Parameters'])[0]
    # print tests
    # getinstdict = h.getHistEntryValue(['Instrument Parameters'])
    # print(getinstdict, "\n")
    # print(getinstdict["Zero"], "\n")

    # subset dictionary of instrument parameters of interest
    instparams = {
        "Lam": instdict['Lam'],
        "Zero": instdict['Zero'],
        "U": instdict['U'],
        "V": instdict['V'],
        "W": instdict['W'],
        "X": instdict['X'],
        "Y": instdict['Y'],
        "Z": instdict['Z'],
        # "SH/L": instdict['SH/L'],
    }
    print(ip)

    # populating list of refinement flags already active
    for param, val in ip.items():
        # set instrument choices dict for UI
        if isinstance(val[2], bool):
            ic[param] = param
            if val[2] is True:
                irl.append(param)

    return irl, ip, ic, srl, sp, sc
"""


def gsas_load_gpx(inputgpxfile):
    """loads gpx from input file and saves it to output file
        the current project is in outputfile so the loaded ones
        from the galaxy history remain unchanged"""
    gpx = G2sc.G2Project(gpxfile=inputgpxfile, newgpx="output.gpx")
    gpx.save()
    return gpx
