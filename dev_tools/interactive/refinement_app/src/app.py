# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
from shinywidgets import render_plotly
from viewmodel import (
    histdata,
    gpx_choices,
    phase_choices,
    hist_choices,
    view_hist_choices,
    view_proj_choices,
    inst_param_dict,
    samp_param_dict,
    sampleparams,
    instparams,
    background_functions,
    sampUIlist,
    plot_powder,
    updatehistory,
    loadproject,
    viewproj,
    loadphase,
    loadhist,
    viewhist,
    load_bkg_data,
    set_bkg_func,
    set_bkg_refine,
    set_bkg_coefs,
    build_bkg_coef_df,
    save_bkg_coefs,
    submitout,
    atomdata,
    saveatomtable,
    showphaseconstr,
    build_constraints_df,
    add_constr,
    remove_constraint,
    updatenav,
    save_inst_params,
    save_samp_params,
    # view_tool_inputs,
)

ui.page_opts(title="GSASII refinement", fillable=True)

with ui.navset_hidden(id="tab"):
    # hidden can be switched to a menu or pillset, so the further nav_menu
    # elements can be left alone if we want to change it later.
    with ui.nav_menu("Powder data"):
        with ui.nav_panel("Background", value="Background"):
            ui.input_select(
                "background_function",
                "Background function",
                background_functions,
                selected=None,
            )
            ui.input_checkbox("bkg_refine", "refine", False)

            ui.input_numeric(
                "num_bkg_coefs",
                "Number of Coefficients",
                value=0,
            )

            @reactive.effect
            @reactive.event(input.background_function)
            def app_bkg_func():
                set_bkg_func(input.selecthist(), input.background_function())

            @reactive.effect
            @reactive.event(input.bkg_refine)
            def app_bkg_ref():
                set_bkg_refine(input.selecthist(), input.bkg_refine())

            @reactive.effect
            @reactive.event(input.num_bkg_coefs)
            def app_bkg_coefs():
                set_bkg_coefs(input.selecthist(), input.num_bkg_coefs())

            @reactive.effect
            @reactive.event(input.save_bkg_coefs)
            def app_save_bkg_coefs():
                coefs = bkg_coeff_df.data_view()["Background Coefficients"].tolist()
                save_bkg_coefs(input.selecthist(), coefs)

            @render.code
            @reactive.event(
                input.loadgpx,
                input.selecthist,
                input.background_function,
                input.bkg_refine,
                input.num_bkg_coefs,
                input.save_bkg_coefs,
            )
            def bkg_data():
                return load_bkg_data(input.selecthist())

            @render.data_frame
            @reactive.event(
                input.loadgpx,
                input.selecthist,
                input.num_bkg_coefs,
                input.save_bkg_coefs,
            )
            def bkg_coeff_df():
                return render.DataTable(
                    build_bkg_coef_df(input.selecthist()),
                    editable=True,
                    height=None,
                )

            ui.input_action_button("save_bkg_coefs", "Save Background Coefficients")

        with ui.nav_panel("Sample Parameters", value="Sample Parameters"):

            ui.input_selectize(
                "samp_selection",
                "Select sample parameters to refine:",
                samp_param_dict,
                multiple=True,
                selected=None,
            )
            with ui.navset_hidden(id="sample"):
                with ui.nav_panel(""):
                    "Set Sample Parameter values:"

                    # for param, label in samp_param_dict.items():
                    #     ui.input_numeric(param, label, 0)

            ui.input_action_button("savesamp", "save sample parameters")

            @reactive.effect
            @reactive.event(input.savesamp)
            def app_savesamp():
                save_samp_params(input)

            @render.code
            @reactive.event(input.savesamp)
            def app_render_save_samp():
                return sampUIlist(), sampleparams()

        with ui.nav_panel("Instrument Refinements", value="Instrument Parameters"):
            ui.input_selectize(
                "inst_selection",
                "Select instrument parameters to refine:",
                inst_param_dict,
                multiple=True,
                selected=None,
            )

            with ui.navset_hidden(id="instruments"):
                with ui.nav_panel("Instrument Parameter Values"):
                    "Set values:"

            ui.input_action_button("saveinst", "save instrument parameters")

            @reactive.effect
            @reactive.event(input.saveinst)
            def app_saveinst():
                save_inst_params(input)

            @render.code
            @reactive.event(input.saveinst)
            def app_render_save_inst():
                return instparams()

    with ui.nav_panel("Phase", value="Phase"):
        with ui.navset_pill(id="phases"):
            with ui.nav_panel("general", value="phasegen"):
                "general"
            with ui.nav_panel("data", value="phasedata"):
                "data"
            with ui.nav_panel("atoms", value="atoms"):

                @render.data_frame
                @reactive.event(input.loadgpx, input.selectphase, input.saveatoms)
                def renderatomtable():
                    return render.DataTable(
                        atomdata(input.selectphase()), editable=True, height=None,
                    )

                ui.input_action_button("saveatoms", "Save atoms changes")

                @reactive.effect
                @reactive.event(input.saveatoms)
                def app_saveatomtable():
                    data = renderatomtable.data_view()
                    saveatomtable(data, input.selectphase())

    with ui.nav_menu("Project"):
        with ui.nav_panel("Notebook", value="Notebook"):
            "Notebook"
        with ui.nav_panel("Controls", value="Controls"):
            "Controls"
        with ui.nav_panel("Constraints", value="Constraints"):

            with ui.layout_column_wrap():
                with ui.card():
                    ui.card_header("Add new constraint")
                    constraint_types = {"eqv": "equivalence", "eqn": "equation"}
                    ui.input_select("constr_type", "constraint type", constraint_types)

                    @render.data_frame
                    def new_constr():
                        codes = render_constr_table.data_view(selected=True)[["code"]]
                        codes["coefficients"] = 1
                        return render.DataTable(codes, height=None, editable=True)

                    ui.input_action_button("add_constr", "add constraint")

                    @render.data_frame
                    @reactive.event(input.add_constr, input.loadgpx, input.popconstr)
                    def app_showphaseconstr():
                        return render.DataTable(
                            showphaseconstr(),
                            height=None,
                            width="100%",
                            selection_mode="row",
                        )

                    @reactive.effect
                    @reactive.event(input.add_constr)
                    def app_add_constr():
                        constr = new_constr.data_view()
                        if len(constr.index) >= 2:
                            add_constr(input.constr_type(), constr, render_constr_table.data())

                    ui.input_action_button("popconstr", "remove constraint")

                    @reactive.effect
                    @reactive.event(input.popconstr)
                    def app_remove_constr():
                        constr_df = app_showphaseconstr.data_view(selected=True)[
                            ["current constraints"]
                        ]
                        if not constr_df.empty:
                            constr_val = constr_df["current constraints"].loc[
                                constr_df.index[0]
                            ]
                            all_constr = app_showphaseconstr.data()
                            constr_id = all_constr.index[
                                all_constr["current constraints"] == constr_val
                            ].tolist()
                            remove_constraint(constr_id[0])

                with ui.card():
                    ui.card_header("select constraint parameters")

                    @render.data_frame
                    def render_constr_table():
                        pn = input.selectphase()
                        constr_df = build_constraints_df(pn)
                        return render.DataTable(
                            constr_df, selection_mode="rows", filters=True
                        )

        with ui.nav_panel("Restraints", value="Restraints"):
            "Restraints"
        with ui.nav_panel("Rigid Bodies", value="Rigid Bodies"):
            "Rigid bodies"

# separate always visible section for plots
with ui.navset_pill(id="plot"):
    with ui.nav_panel("plots", value="plots"):

        @render_plotly
        def plot():
            fig = plot_powder(input.selecthist())
            return fig

    with ui.nav_panel("History", value="hist"):

        @render.data_frame
        @reactive.event(input.updatehist)
        def renderupdatehistory():
            return render.DataTable(histdata())


with ui.sidebar(bg="#f8f8f8", position="left"):

    ui.input_action_button("updatehist", "update history")

    ui.input_select("selectgpx", "load GSASII project:", gpx_choices)
    ui.input_action_button("loadgpx", "Load project")

    ui.input_select("viewprojdata", "Project", view_proj_choices)

    ui.input_action_button("viewproj", "View project")

    @reactive.effect
    @reactive.event(input.viewprojdata, input.viewproj)
    def app_updateprojnav():
        tab = input.viewprojdata()
        updatenav(tab)

    ui.input_select("selectphase", "Phase", phase_choices)
    ui.input_action_button("viewphase", "View phase")

    @reactive.effect
    @reactive.event(input.viewphase)
    def app_updatephasenav():
        tab = "Phase"
        updatenav(tab)

    ui.input_select("selecthist", "Histogram", hist_choices)
    ui.input_select("viewhistdata", "View Histogram data", view_hist_choices)
    ui.input_action_button("viewhistogram", "View histogram")

    @reactive.effect
    @reactive.event(input.viewhistdata, input.viewhistogram)
    def app_updatehistnav():
        tab = input.viewhistdata()
        updatenav(tab)

    ui.input_action_button("submit", "Refine")

    @reactive.effect
    @reactive.event(input.updatehist, ignore_none=False)
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
        submitout()
