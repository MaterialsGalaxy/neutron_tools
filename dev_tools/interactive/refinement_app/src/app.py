# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
from shinywidgets import render_plotly
from viewmodel import (
    hist_data,
    gpx_choices,
    phase_choices,
    hist_choices,
    view_hist_choices,
    view_proj_choices,
    inst_param_dict,
    samp_param_dict,
    gpx,
    inst_params,
    background_functions,
    samp_UI_list,
    plot_powder,
    set_hist_limits,
    update_history,
    load_project,
    view_proj,
    load_phase,
    load_histogram,
    view_hist,
    load_bkg_data,
    set_bkg_func,
    set_bkg_refine,
    set_bkg_coefs,
    build_bkg_coef_df,
    save_bkg_coefs,
    submit_out,
    atom_data,
    save_atom_table,
    show_phase_constr,
    build_constraints_df,
    add_constr,
    remove_constraint,
    update_nav,
    save_inst_params,
    build_sample_df,
    save_sample_parameters,
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
                set_bkg_func(input.select_hist(), input.background_function())

            @reactive.effect
            @reactive.event(input.bkg_refine)
            def app_bkg_ref():
                set_bkg_refine(input.select_hist(), input.bkg_refine())

            @reactive.effect
            @reactive.event(input.num_bkg_coefs)
            def app_bkg_coefs():
                set_bkg_coefs(input.select_hist(), input.num_bkg_coefs())

            @reactive.effect
            @reactive.event(input.save_bkg_coefs)
            def app_save_bkg_coefs():
                coefs = bkg_coeff_df.data_view()["Background Coefficients"].tolist()
                save_bkg_coefs(input.select_hist(), coefs)

            @render.code
            @reactive.event(
                input.load_gpx,
                input.select_hist,
                input.background_function,
                input.bkg_refine,
                input.num_bkg_coefs,
                input.save_bkg_coefs,
            )
            def bkg_data():
                return load_bkg_data(input.select_hist())

            @render.data_frame
            @reactive.event(
                input.load_gpx,
                input.select_hist,
                input.num_bkg_coefs,
                input.save_bkg_coefs,
            )
            def bkg_coeff_df():
                return render.DataTable(
                    build_bkg_coef_df(input.select_hist()),
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

            @render.data_frame
            @reactive.event(
                input.load_gpx,
                input.select_hist,
                input.view_histogram,
                )
            def app_render_sample_df():
                sample_df = build_sample_df(input.select_hist())
                return render.DataTable(
                    sample_df,
                    editable=True,
                    height=None,
                )
            
            ui.input_action_button("save_samp", "save sample parameters")

            @reactive.effect
            @reactive.event(
                input.save_samp
            )
            def app_save_sample_parameters():
                input_sample_df = app_render_sample_df.data_view()
                save_sample_parameters(input.select_hist(), input_sample_df, input.samp_selection())


            @render.code
            @reactive.event(input.save_samp)
            def app_render_save_samp():
                return samp_UI_list(), gpx().histogram(input.select_hist()).getHistEntryValue(["Sample Parameters"])

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

            ui.input_action_button("save_inst", "save instrument parameters")

            @reactive.effect
            @reactive.event(input.save_inst)
            def app_save_inst():
                save_inst_params(input)

            @render.code
            @reactive.event(input.save_inst)
            def app_render_save_inst():
                return inst_params()

    with ui.nav_panel("Phase", value="Phase"):
        with ui.navset_pill(id="phases"):
            with ui.nav_panel("general", value="phasegen"):
                "general"
            with ui.nav_panel("data", value="phasedata"):
                "data"
            with ui.nav_panel("atoms", value="atoms"):

                @render.data_frame
                @reactive.event(
                    input.load_gpx,
                    input.select_phase,
                    input.view_phase,
                    input.save_atoms,
                )
                def render_atom_table():
                    return render.DataTable(
                        atom_data(input.select_phase()),
                        editable=True,
                        height=None,
                    )

                ui.input_action_button("save_atoms", "Save atoms changes")

                @reactive.effect
                @reactive.event(input.save_atoms)
                def app_save_atom_table():
                    data = render_atom_table.data_view()
                    save_atom_table(data, input.select_phase())

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
                    @reactive.event(input.add_constr, input.load_gpx, input.pop_constr)
                    def app_show_phase_constr():
                        return render.DataTable(
                            show_phase_constr(),
                            height=None,
                            width="100%",
                            selection_mode="row",
                        )

                    @reactive.effect
                    @reactive.event(input.add_constr)
                    def app_add_constr():
                        constr = new_constr.data_view()
                        if len(constr.index) >= 2:
                            add_constr(
                                input.constr_type(), constr, render_constr_table.data()
                            )

                    ui.input_action_button("pop_constr", "remove constraint")

                    @reactive.effect
                    @reactive.event(input.pop_constr)
                    def app_remove_constr():
                        constr_df = app_show_phase_constr.data_view(selected=True)[
                            ["current constraints"]
                        ]
                        if not constr_df.empty:
                            constr_val = constr_df["current constraints"].loc[
                                constr_df.index[0]
                            ]
                            all_constr = app_show_phase_constr.data()
                            constr_id = all_constr.index[
                                all_constr["current constraints"] == constr_val
                            ].tolist()
                            remove_constraint(constr_id[0])

                with ui.card():
                    ui.card_header("select constraint parameters")

                    @render.data_frame
                    def render_constr_table():
                        pn = input.select_phase()
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
            fig = plot_powder(input.select_hist(), input.limits())
            return fig

        ui.input_slider("limits", "Set limits", min=0, max=1, value=[0, 1])

        @reactive.effect
        @reactive.event(input.limits)
        def app_set_limits():
            set_hist_limits(input.select_hist(), input.limits())

    with ui.nav_panel("History", value="hist"):

        @render.data_frame
        @reactive.event(input.update_history, input.load_gpx)
        def render_update_history():
            return render.DataTable(hist_data())


with ui.sidebar(bg="#f8f8f8", position="left"):

    ui.input_action_button("update_history", "update history")

    ui.input_select("select_gpx", "load GSASII project:", gpx_choices)
    ui.input_action_button("load_gpx", "Load project")

    ui.input_select("view_project_data", "Project", view_proj_choices)

    ui.input_action_button("view_proj", "View project")

    @reactive.effect
    @reactive.event(input.view_project_data, input.view_proj)
    def app_updateprojnav():
        tab = input.view_project_data()
        update_nav(tab)

    ui.input_select("select_phase", "Phase", phase_choices)
    ui.input_action_button("view_phase", "View phase")

    @reactive.effect
    @reactive.event(input.view_phase, input.select_phase)
    def app_update_phase_nav():
        tab = "Phase"
        update_nav(tab)

    ui.input_select("select_hist", "Histogram", hist_choices)
    ui.input_select("view_hist_data", "View Histogram data", view_hist_choices)
    ui.input_action_button("view_histogram", "View histogram")

    @reactive.effect
    @reactive.event(input.view_hist_data, input.view_histogram)
    def app_update_history_nav():
        tab = input.view_hist_data()
        update_nav(tab)

    ui.input_action_button("submit", "Refine")

    @reactive.effect
    @reactive.event(input.update_history, ignore_none=False)
    def app_update_history():
        update_history()

    @reactive.effect
    @reactive.event(input.load_gpx)
    def app_load_project():
        id = input.select_gpx()
        load_project(id)

    @reactive.effect
    @reactive.event(input.view_project_data)
    def app_view_proj():
        view_proj()

    @reactive.effect
    @reactive.event(input.select_phase)
    def app_load_phase():
        load_phase()

    @reactive.effect
    @reactive.event(input.select_hist)
    def app_load_histogram():
        load_histogram(input.select_hist())

    @reactive.effect
    @reactive.event(input.view_hist_data)
    def app_view_hist():
        view_hist()

    @reactive.effect
    @reactive.event(input.submit)
    def ui_submit_out():
        submit_out()
