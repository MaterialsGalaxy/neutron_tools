# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
from viewmodel import (
    histdata,
    gpx_choices,
    plot_powder,
    updatehistory,
    loadproject,
    submitout,
    submit_message,
)

ui.page_opts(title="GSASII refinement: instrument parameters", fillable=True)

with ui.navset_card_pill(id="tab"):
    with ui.nav_panel("powder data"):

        @render.plot(alt="A histogram")
        @reactive.event(input.loadgpx)
        def plot():
            plot_powder()

    with ui.nav_panel("B"):
        ui.input_action_button("updatehist", "update history")
        ui.input_select("selectgpx", "load GSASII project:",
                        gpx_choices)
        ui.input_action_button("loadgpx", "Load project")

        @reactive.effect
        @reactive.event(input.updatehist)
        def app_updatehistory():
            updatehistory()

        @render.data_frame
        @reactive.event(input.updatehist)
        def renderupdatehistory():
            return render.DataTable(histdata())

        @reactive.effect
        @reactive.event(input.loadgpx)
        def app_loadproject():
            loadproject(input)

    with ui.nav_menu("Other links"):
        with ui.nav_panel("D"):
            "Page D content"

        "----"
        "Description:"
        with ui.nav_control():
            ui.a("Shiny", href="https://shiny.posit.co", target="_blank")


with ui.sidebar(bg="#f8f8f8", position='left'):
    ui.input_selectize(
        "inst_selection",
        "Select instrument parameters to refine:",
        {"Lam": "Lam", "Zero": "Zero", "U": "U", "V": "V", "W": "W",
         "X": "X", "Y": "Y", "Z": "Z"},
        multiple=True,
        selected=None,
    )

    ui.input_numeric("Lam", "Lam", 0)
    ui.input_numeric("Zero", "Zero", 0)
    ui.input_numeric("U", "U", 0)
    ui.input_numeric("V", "V", 0)
    ui.input_numeric("W", "W", 0)
    ui.input_numeric("X", "X", 0)
    ui.input_numeric("Y", "Y", 0)
    ui.input_numeric("Z", "Z", 0)
    # ui.input_numeric("SHL", "SH/L", instparams["SH/L"][0])

    ui.input_selectize(
        "samp_selection",
        "Select sample parameters to refine:",
        {"Scale": "Scale", "DisplaceX": "Sample X displ. perp. to beam",
            "DisplaceY": "Sample Y displ. prll. to beam",
            "Absorption": "Sample Absorption"},
        multiple=True,
        selected=None,
    )

    ui.input_numeric("Scale", "histogram scale factor",
                     0)
    ui.input_numeric("DisplaceX", "Sample X displ. perp. to beam",
                     0)
    ui.input_numeric("DisplaceY", "Sample Y displ. prll. to beam",
                     0)
    ui.input_numeric("Absorption", "Sample Absorption",
                     0)

    ui.input_action_button("submit", "submit")

    @reactive.effect
    @reactive.event(input.submit)
    def ui_submitout():
        submitout(input)

    @render.text
    @reactive.event(input.submit)
    def submit_text():
        # print out the new refinement parameters
        return submit_message()
