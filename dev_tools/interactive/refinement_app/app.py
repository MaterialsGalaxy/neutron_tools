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
    inst_param_dict = {"Lam": "Lam", "Zero": "Zero", "U": "U", "V": "V",
                       "W": "W", "X": "X", "Y": "Y", "Z": "Z"}
    ui.input_selectize(
        "inst_selection",
        "Select instrument parameters to refine:",
        inst_param_dict,
        multiple=True,
        selected=None,
    )
    for param, label in inst_param_dict.items():
        ui.input_numeric(param, label, 0)

    samp_param_dict = {"Scale": "Scale",
                       "DisplaceX": "Sample X displ. perp. to beam",
                       "DisplaceY": "Sample Y displ. prll. to beam",
                       "Absorption": "Sample Absorption"}
    ui.input_selectize(
        "samp_selection",
        "Select sample parameters to refine:",
        samp_param_dict,
        multiple=True,
        selected=None,
    )

    for param, label in samp_param_dict.items():
        ui.input_numeric(param, label, 0)

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
