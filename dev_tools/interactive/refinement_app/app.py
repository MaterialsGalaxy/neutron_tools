# import matplotlib.pyplot as plt
# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
# import sys
# import os
from gsasIImodel import (
    instreflist,
    instparams,
    sampreflist,
    sampleparams,
)

ui.page_opts(title="GSASII refinement: instrument parameters", fillable=True)

ui.input_selectize(
    "inst_selection",
    "Select instrument parameters to refine:",
    {"Lam": "Lam", "Zero": "Zero", "U": "U", "V": "V", "X": "X", "Y": "Y",
        "Z": "Z"},
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
# ui.input_numeric("SHL", "SH/L", instparams["SH/L"][0])


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
        result = "Refining sample parameters: {sref} \n\
                  with values {svals} \n\
                  Refining instrument parameters {iref} \n\
                  with values is {ivals}"\
                  .format(sref=sampreflist, svals=sampleparams,
                          iref=instreflist, ivals=instparams)
        return result
