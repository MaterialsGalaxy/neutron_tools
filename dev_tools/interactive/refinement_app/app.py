# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
from viewmodel import (
    histdata,
    gpx_choices,
    phase_choices,
    hist_choices,
    view_hist_choices,
    view_proj_choices,
    plot_powder,
    updatehistory,
    loadproject,
    viewproj,
    loadphase,
    loadhist,
    viewhist,
    submitout,
    atomdata,
    saveatomtable,
)

ui.page_opts(title="GSASII refinement: instrument parameters", fillable=True)

with ui.navset_card_pill(id="tab"):
    with ui.nav_panel("plots"):

        @render.plot(alt="A histogram")
        @reactive.event(input.loadgpx)
        def plot():
            plot_powder()

    with ui.nav_panel("History"):

        @render.data_frame
        @reactive.event(input.updatehist)
        def renderupdatehistory():
            return render.DataTable(histdata())

    with ui.nav_panel("Powder data"):
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

    with ui.nav_panel("Phase"):
        with ui.navset_card_pill(id="phase_sections"):
            with ui.nav_panel("general"):
                "general"
            with ui.nav_panel("data"):
                "data"
            with ui.nav_panel("atoms"):
                ui.input_action_button("updateatoms", "update phase atoms")

                @render.data_frame
                @reactive.event(input.updateatoms)
                def renderatomtable():
                    return render.DataTable(atomdata(input.selectphase()),
                                            editable=True)

                ui.input_action_button("saveatoms", "Save atoms changes")

                @reactive.effect
                @reactive.event(input.saveatoms)
                def app_saveatomtable():
                    data = renderatomtable.data_view()
                    saveatomtable(data, input.selectphase())

    with ui.nav_panel("Project"):
        "what else"
    with ui.nav_menu("Other links"):
        with ui.nav_panel("D"):
            "Page D content"

        "----"
        "Description:"
        with ui.nav_control():
            ui.a("Shiny", href="https://shiny.posit.co", target="_blank")

with ui.sidebar(bg="#f8f8f8", position='left'):

    ui.input_action_button("updatehist", "update history")

    ui.input_select("selectgpx", "load GSASII project:",
                    gpx_choices)
    ui.input_action_button("loadgpx", "Load project")
    ui.input_select("viewprojdata", "View project data", view_proj_choices)

    ui.input_select("selectphase", "Phase", phase_choices)
    ui.input_select("selecthist", "Histogram", hist_choices)
    ui.input_select("viewhistdata", "View Histogram data", view_hist_choices)

    ui.input_action_button("submit", "submit")

    @reactive.effect
    @reactive.event(input.updatehist)
    def app_updatehistory():
        updatehistory()

    @reactive.effect
    @reactive.event(input.loadgpx)
    def app_loadproject():
        id = input.selectgpx()
        loadproject(id)

    @reactive.effect
    @reactive.event(input.viewprojdata)
    def app_viewproj():
        viewproj()

    @reactive.effect
    @reactive.event(input.selectphase)
    def app_loadphase():
        loadphase()

    @reactive.effect
    @reactive.event(input.selecthist)
    def app_loadhist():
        loadhist(input.selecthist())

    @reactive.effect
    @reactive.event(input.viewhistdata)
    def app_viewhist():
        viewhist()

    @reactive.effect
    @reactive.event(input.submit)
    def ui_submitout():
        submitout(input)
