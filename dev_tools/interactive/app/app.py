import matplotlib.pyplot as plt
import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
import os
import shutil
import gxhistory

with ui.sidebar():
    ui.input_slider("n", "N", 0, 100, 20)


ui.input_action_button("submit", "submit to history")

@render.text
@reactive.event(input.submit)
def counter():
    if input.submit() == 1:
        gxhistory.put("outfile.txt")
    return "submitted"


@render.text
def text():
    datafile = open("infile.txt", "r")
    shutil.copy("infile.txt", "/var/shiny-server/shiny_test/work/output.txt")
    outputfile = open("/var/shiny-server/shiny_test/work/output.txt", "r")
    data = outputfile.read()
    if data is None:
        data = " environment variables not found"
    datafile.close()
    outputfile.close()
    return data


@render.text
def text2():
    environvars = os.environ['HISTORY_ID']
    if environvars is None:
        result = " environment variables not found"
    else:
        result = environvars
    return result
