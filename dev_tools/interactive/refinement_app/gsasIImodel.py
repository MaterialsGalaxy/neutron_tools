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
    """
    loads a subset of sample and isntrument parameters and refinement
    flags of interest for the UI. Could be extended to everything.
    """
    h = gpx.histogram(histname)

    # dictionary of subset of sample parameters values of interest
    sampleparams = {
        "Scale": h.getHistEntryValue(['Sample Parameters', 'Scale']),
        "DisplaceX": h.getHistEntryValue(['Sample Parameters', 'DisplaceX']),
        "DisplaceY": h.getHistEntryValue(['Sample Parameters', 'DisplaceY']),
        "Absorption": h.getHistEntryValue(['Sample Parameters', 'Absorption']),
    }
    sampreflist = []
    instreflist = []

    # populating list of sample refinements that are already active
    for param in sampleparams:
        if sampleparams[param][1] is True:
            sampreflist.append(param)

    # debugging print statements
    print(h.getHistEntryValue(['Instrument Parameters'])[0]['Lam'])
    print(h.getHistEntryValue(['Instrument Parameters']))

    # full instrument parameter dictionary
    instdict = h.getHistEntryValue(['Instrument Parameters'])[0]
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
    print(instparams)

    # populating list of refinement flags already active
    for param in instparams:
        if instparams[param][2] is True:
            instreflist.append(param)
    return instreflist, instparams, sampreflist, sampleparams


def gsas_load_gpx(inputgpxfile):
    """loads gpx from input file and saves it to output file
        the current project is in outputfile so the loaded ones
        from the galaxy history remain unchanged"""
    gpx = G2sc.G2Project(gpxfile=inputgpxfile, newgpx="output.gpx")
    gpx.save()
    return gpx
