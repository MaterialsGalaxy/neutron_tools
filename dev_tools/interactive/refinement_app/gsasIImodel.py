import sys
# import os
import numpy as np
sys.path.append("/srv/shiny-server/GSASII")
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")
import GSASIIscriptable as G2sc  # type: ignore


def load_phase_constraints(gpx):
    # load the constraints previously added to the project
    # seems to not be readable
    phase_constraint_list = gpx.get_Constraints('Phase')
    return phase_constraint_list


def hist_export(gpx):
    # gpx = G2sc.G2Project(gpx_file)
    x = np.array(gpx.histogram(0).getdata("X"))
    y = np.array(gpx.histogram(0).getdata("Yobs"))
    ycalc = np.array(gpx.histogram(0).getdata("Ycalc"))
    dy = np.array(gpx.histogram(0).getdata("Residual"))
    bkg = np.array(gpx.histogram(0).getdata("Background"))

    return x, y, ycalc, dy, bkg
    # for i, h in enumerate(gpx.histograms()):
    # hfil = os.path.splitext(gpx_file)[0]+'_'+str(i)  # file to write
    # print('\t', h.name, hfil+'.csv')
    # h.Export(hfil, '.csv')


def gsas_load_gpx(inputgpxfile):
    gpx = G2sc.G2Project(gpxfile=inputgpxfile, newgpx="output.gpx")
    gpx.save()
    # get the sample and instrument parameters from previous refinement in
    # dictionaries.

    # h.getHistEntryValue(['Sample Parameters', 'Type'], 'Bragg-Brentano')
    # histnum = len(gpx.histograms())
    h = gpx.histograms()[0]

    sampleparams = {
        "Scale": h.getHistEntryValue(['Sample Parameters', 'Scale']),
        "DisplaceX": h.getHistEntryValue(['Sample Parameters', 'DisplaceX']),
        "DisplaceY": h.getHistEntryValue(['Sample Parameters', 'DisplaceY']),
        "Absorption": h.getHistEntryValue(['Sample Parameters', 'Absorption']),
    }
    sampreflist = []
    instreflist = []

    for param in sampleparams:
        if sampleparams[param][1] is True:
            sampreflist.append(param)
    print(h.getHistEntryValue(['Instrument Parameters'])[0]['Lam'])
    print(h.getHistEntryValue(['Instrument Parameters']))

    instdict = h.getHistEntryValue(['Instrument Parameters'])[0]
    # print tests
    # getinstdict = h.getHistEntryValue(['Instrument Parameters'])
    # print(getinstdict, "\n")
    # print(getinstdict["Zero"], "\n")

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

    for param in instparams:
        if instparams[param][2] is True:
            instreflist.append(param)
    return gpx, instreflist, instparams, sampreflist, sampleparams


# define function to write to gpx project
def saveParameters(gpx,
                   instreflist,
                   instparams,
                   sampreflist,
                   sampleparams):
    """
    saves new instrument and sample parameters to a chosen GSAS project file.
    """
    # gpx = G2sc.G2Project(gpxfile=gpxfile)
    h = gpx.histograms()[0]

    # set new instrument refinements.
    # Doesnt remove unselected parameters from refinement

    instrefdict = {'Instrument Parameters': instreflist}
    h.set_refinements(instrefdict)
    print(instreflist, "\n")
    print(instrefdict, "\n")
    # set new instrument parameters

    instdictfull = h.getHistEntryValue(['Instrument Parameters'])
    for param in instreflist:
        instparams[param][2] = True
    for param in instparams:
        print(instparams, "\n")
        print(param, "\n")
        print(instparams[param], "\n")
        instdictfull[0][param] = instparams[param]

    h.setHistEntryValue(['Instrument Parameters'],
                        instdictfull)

    # set new sample parameters and refinements

    for param in sampreflist:
        sampleparams[param][1] = True
    for param in sampleparams:
        h.setHistEntryValue(['Sample Parameters', param], sampleparams[param])
    gpx.save()
# instrument parameters is actually a list of dictionaries.
# only concerned with [0]
