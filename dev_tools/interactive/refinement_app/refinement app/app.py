import matplotlib.pyplot as plt
import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
import sys
import os

sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")
# needed to "find" GSAS-II modules
# sys.path.append('/home/mkscd/miniconda3/envs/GSASII/bin')
# needed to "find" GSAS-II modules
import GSASIIscriptable as G2sc  # type: ignore
test_proj_dir = "YAG.gpx"

gpx = G2sc.G2Project(gpxfile=test_proj_dir, newgpx="test_proj.gpx")
gpx.save()
# get the sample and instrument parameters from previous refinement in
# dictionaries.

ui.page_opts(title="GSASII refinement: instrument parameters", fillable=True)

# h.getHistEntryValue(['Sample Parameters', 'Type'], 'Bragg-Brentano')
histnum = len(gpx.histograms())
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
print(h.getHistEntryValue(['Sample Parameters']))

instdict = h.getHistEntryValue(['Instrument Parameters'])[0]

instparams = {
    "Lam": instdict['Lam'],
    "Zero": instdict['Zero'],
    "U": instdict['U'],
    "V": instdict['V'],
    "W": instdict['W'],
    "X": instdict['X'],
    "Y": instdict['Y'],
    "Z": instdict['Z'],
    "SH/L": instdict['SH/L'],
}
print(instparams)

for param in instparams:
    if instparams[param][1] is True:
        instreflist.append(param)

ui.input_selectize(
    "inst_selection",
    "Select instrument parameters to refine:",
    {"Lam": "Lam", "Zero": "Zero", "U": "U", "V": "V", "X": "X", "Y": "Y",
        "Z": "Z", "SHL": "SH/L"},
    multiple=True,
    selected=instreflist,
)

ui.input_numeric("Lam", "Lam", instparams["Lam"][0])
ui.input_numeric("Zero", "Zero", instparams["Zero"][0])
ui.input_numeric("U", "U", instparams["U"][0])
ui.input_numeric("V", "V", instparams["V"][0])
ui.input_numeric("W", "W", instparams["W"][0])
ui.input_numeric("X", "X", instparams["X"][0])
ui.input_numeric("Y", "Y", instparams["Y"][0])
ui.input_numeric("Z", "Z", instparams["Z"][0])
ui.input_numeric("SHL", "SH/L", instparams["SH/L"][0])


ui.input_selectize(
    "samp_selection",
    "Select sample parameters to refine:",
    {"Scale": "Scale", "DisplaceX": "Sample X displ. perp. to beam",
        "DisplaceY": "Sample Y displ. prll. to beam",
        "Absorption": "Sample Absorption"},
    multiple=True,
    selected=sampreflist,
)

ui.input_numeric("Scale", "histogram scale factor",
                 sampleparams["Scale"][0])
ui.input_numeric("DisplaceX", "Sample X displ. perp. to beam",
                 sampleparams["DisplaceX"][0])
ui.input_numeric("DisplaceY", "Sample Y displ. prll. to beam",
                 sampleparams["DisplaceY"][0])
ui.input_numeric("Absorption", "Sample Absorption",
                 sampleparams["Absorption"][0])

ui.input_action_button("submit", "submit")


@render.text()
@reactive.event(input.submit)
def submitout():
    if input.submit() > 0:
        sampreflist = input.samp_selection()
        instreflist = input.inst_selection()

        for param in sampleparams:
            sampleparams[param] = getattr(input, param)()

        for param in instparams:
            instparams[param] = getattr(input, param)()
        return f"{instparams}"


@render.text
def text():
    datafile = open("infile.txt", "r")
    data = datafile.read()
    datafile.close()
    return data
