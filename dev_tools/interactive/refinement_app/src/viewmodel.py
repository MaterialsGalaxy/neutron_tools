from shiny.express import ui
from shiny import reactive
from deepdiff import DeepDiff, Delta
import pandas as pd
import gxhistory
import os
import numpy as np
from gsasIImodel import (
    hist_export,
    gsas_load_gpx,
    load_phase_constraints,
    load_histogram_parameters,
    GSAS2Project,
)
import plotly.express as px
import typing
import time

"""contains all reactive events functions and variables
and processes all logic from the ui, GSASII and galaxy history models.
note functions defined here cannot directly access inputs from view.
these have to be passed as inputs to the function."""

# reactive value parameters for anything that needs to be passed on
# as a side effect from reactive functions
gpx = reactive.value()
og_gpx = reactive.value()
current_gpx_fname = reactive.value()
inst_ref_list = reactive.value()
inst_params = reactive.value(None)
samp_ref_list = reactive.value()
sample_params = reactive.value(None)
input_gpx_file = reactive.value()
inst_choices = reactive.value()
samp_choices = reactive.value()
samp_UI_list = reactive.value([])

num_bkg_coefs = reactive.value()
current_bkg_func = reactive.value()

x = reactive.value()
y = reactive.value()
ycalc = reactive.value()
dy = reactive.value()
bkg = reactive.value()

hist_data = reactive.value()
constraints = reactive.value()

current_gpx_id = reactive.value()

# initial values for sidebar selections when no project is loaded
# reactive values for when projects are loaded
gpx_choices = {"init": "update the history before loading a new project"}
select_gpx_choices = reactive.value(gpx_choices)

phase_choices = {"init": "Load a project before selecting a phase"}
select_phase_choices = reactive.value(phase_choices)

hist_choices = {"init": "Load a project before selecting a histogram"}
select_hist_choices = reactive.value(hist_choices)
view_hist_choices = {"init": "Load a project before selecting a histogram"}
select_view_hist = reactive.value(view_hist_choices)

view_proj_choices = {
    "Notebook": "Notebook",
    "Controls": "Controls",
    "Constraints": "Constraints",
    "Restraints": "Restraints",
    "Rigid Bodies": "Rigid Bodies",
}

inst_param_dict = {
    "Lam": "Lam",
    "Zero": "Zero",
    "U": "U",
    "V": "V",
    "W": "W",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
}

samp_param_dict = {
    "Scale": "Scale",
    "DisplaceX": "Sample X displ. perp. to beam",
    "DisplaceY": "Sample Y displ. prll. to beam",
    "Absorption": "Sample Absorption",
}

background_functions = {
    "chebyschev": "chebyschev",
    "chebyschev-1": "chebyschev-1",
    "cosine": "cosine",
    "Q^2 power series": "Q^2 power series",
    "Q^-2 power series": "Q^-2 power series",
    "lin interpolate": "lin interpolate",
    "inv interpolate": "inv interpolate",
    "log interpolate": "log interpolate",
}


def update_nav(tab: str) -> None:
    """
    updates the tab viewed in the UI.
    The main UI uses a hidden navset so the menus
    can be navigated using the sidebar

    """
    # set the tab in the main view from the sidebar controls
    ui.update_navs(id="tab", selected=tab)


def add_constr(ctype: str, df: pd.DataFrame, var_df: pd.DataFrame) -> None:
    """
    wrapper function for adding equivalence or equation constraints
    equation constraints are forced to have a total of 1
    """
    # add constraints to constraints list and to gpx
    constr_vars = df["code"].tolist()
    constr_coefs = df["coefficients"].tolist()

    # validation
    valid = False
    if len(df.index) >= 2:
        vars_valid = set(constr_vars).issubset(set(var_df["code"].tolist()))
        if vars_valid:
            try:
                coefs = [float(c) for c in constr_coefs]
            except Exception:
                print("invalid coefficients")
            else:
                valid = True
        else:
            print("invalid parameter name")

    # add the constriants to the gpx
    if valid:
        if ctype == "eqv":
            constraints().append(["EQUIV", constr_vars, coefs])
            gpx().add_EquivConstr(constr_vars, multlist=coefs)
        elif ctype == "eqn":
            constraints().append(["CONST", constr_vars, coefs])
            gpx().add_EqnConstr(1, constr_vars, multlist=coefs)


def build_constraints_df(phase_name: str) -> pd.DataFrame:
    """
    builds/populates the Dataframe of possible parameters
    to choose for phase constraints
    used so users can make selections for constraint inputs
    """
    # initialise constraints
    constraint_cols = ["code", "phase", "parameter", "atom"]
    phase_constr_df = pd.DataFrame(columns=constraint_cols)

    phase = gpx().phase(phase_name)

    # list of selectable parameter types. to be extended
    parameters = ["Afrac", "AUiso"]

    # populate dataframe with all possible combinations of
    # parameter type and Atom label
    for param in parameters:
        i = 0
        for atom in phase.atoms():

            # generate the code GSASII needs for constraint functions
            code = str(phase.id) + "::" + param + ":" + str(i)

            i += 1
            constraint_vals = [code, phase_name, param, atom.label]
            constraint_record = dict(zip(constraint_cols, constraint_vals))
            phase_constr_df = phase_constr_df._append(
                constraint_record, ignore_index=True
            )
    return phase_constr_df


def remove_constraint(id: str) -> None:
    constraints = load_phase_constraints(gpx())
    if isinstance(id, int) and id < len(constraints):
        constraints.pop(id)


def show_phase_constr() -> pd.DataFrame:
    """
    TBC reads constraint data from the gpx and re arranges them for UI output
    """
    gpx().index_ids()
    constraints = load_phase_constraints(gpx())
    current_constraints = pd.DataFrame(columns=["current constraints"])
    # rearrange the data for visualisation
    for constraint in constraints:
        # equation constraint
        if constraint[-1] == "c":
            new_entry = "CONST "
            for parameter in constraint:
                if isinstance(parameter, list):
                    var_obj = parameter[1]
                    var_name: str = var_obj.varname()
                    new_entry = new_entry + str(parameter[0]) + "*" + var_name + " + "

            new_entry = new_entry.strip("+ ")
            new_entry = new_entry + " = " + str(constraint[-3])

        # equivalence constraint
        elif constraint[-1] == "e":
            new_entry = "EQUIV "
            for parameter in constraint:
                if isinstance(parameter, list):
                    var_coef = str(parameter[0])
                    var_obj = parameter[1]
                    var_name = var_obj.varname()
                    new_entry = new_entry + var_coef + "*" + var_name + " = "
            new_entry = new_entry.strip("= ")

        # add new entry to dataframe
        current_constraints.loc[len(current_constraints)] = {
            "current constraints": new_entry,
        }

    return current_constraints


def save_atom_table(df: pd.DataFrame, phase_name: str) -> None:
    """
    saves the edited atom dataframe
    currently only saves refinement flag edits to the gpx
    """

    phase = gpx().phase(phase_name)

    for atom in phase.atoms():
        atom_record = df.loc[df["Name"] == atom.label]
        flag = atom_record.iloc[0]["refine"]
        # check_flag = flag.translate({ord(i): None for i in 'FXU'})
        check_flag = flag
        for f in "FXU":
            check_flag = check_flag.replace(f, "", 1)
        if check_flag == "":
            atom.refinement_flags = flag
        else:
            print("invalid flags")


def atom_data(phase_name: str) -> pd.DataFrame:
    """
    generates a pandas dataframe containing data for atoms
    in the selected phase.
    used to render in the phase atom UI.
    """
    phase = gpx().phase(phase_name)

    # initialise the dataframe
    atom_cols = ["Name", "type", "refine", "x", "y", "z", "frac", "multi", "Uiso"]
    atom_frame: pd.DataFrame = pd.DataFrame(columns=atom_cols)

    # populate the dataframe with data from the project
    for atom in phase.atoms():
        atom_vals = [
            atom.label,
            atom.type,
            atom.refinement_flags,
            atom.coordinates[0],
            atom.coordinates[1],
            atom.coordinates[2],
            atom.occupancy,
            atom.mult,
            atom.uiso,
        ]
        atom_record = dict(zip(atom_cols, atom_vals))
        atom_frame = atom_frame._append(atom_record, ignore_index=True)

    return atom_frame


def load_bkg_data(hist_name: str) -> list[list, dict]:
    if hist_name != "init":
        bkg_data: list[list, dict] = gpx().histogram(hist_name).Background
        return bkg_data
    else:
        return None
    # num_bkg_coefs.set()
    # current_bkg_func.set()


def build_bkg_page(hist_name: str) -> None:
    bkg_data = load_bkg_data(hist_name)
    ui.update_select("background_function", selected=bkg_data[0][0])
    ui.update_checkbox("bkg_refine", value=bkg_data[0][1])
    ui.update_numeric("num_bkg_coefs", value=bkg_data[0][2])


def set_bkg_func(hist_name: str, func_name: str) -> None:
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][0] = func_name


def set_bkg_refine(hist_name: str, flag: bool) -> None:
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][1] = flag


def set_bkg_coefs(hist_name: str, num_coefs: int) -> None:
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][2] = num_coefs
        current_coefs = len(bkg_data[0]) - 3
        if num_coefs > current_coefs:
            bkg_data[0] = bkg_data[0] + [np.float64(0.0)] * (num_coefs - current_coefs)


def build_bkg_coef_df(hist_name: str) -> pd.DataFrame:
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        coefs = bkg_data[0][3:]
        bkg_coef_df = pd.DataFrame(coefs, columns=["Background Coefficients"])
        return bkg_coef_df


def save_bkg_coefs(hist_name: str, coefs: list) -> None:
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        try:
            new_coefs = np.float64(coefs)

        except Exception:
            print("invalid coefficient inputs")
        else:
            bkg_data[0][3:] = new_coefs


def build_inst_page() -> None:
    """
    in development
    generate the instrument parameter UI dynamically
    needed as Continuous Wave and Time of Flight experiments
    have different parameters
    """
    # update the refinement flags choices too
    # and filter which inputs to show numerically/text
    ui.update_selectize(
        "inst_selection", choices=inst_choices(), selected=inst_ref_list()
    )
    # previous = "inst_selection"

    # generate the new UI elements
    # Ideally generate all directly from the gsas histogram object's
    # instrument parameter dictionary
    # finds previous element from selector, inserts new element after it
    # requires removing too, unclear how this works

    previous = "instruments"

    # could make a dictionary of param keys to ui labels

    for param, val in inst_params().items():
        if isinstance(val, list):
            if isinstance(val[0], float) or isinstance(val[1], float):
                if param != "SH/L" and param != "Polariz.":

                    ui.insert_ui(
                        ui.input_numeric(id=param, label=param, value=val[1]),
                        selector="#" + previous,
                        where="afterEnd",
                    )
                    previous = param


def build_samp_page() -> None:
    # add updating the flag choices and filter which inputs to show
    # numerically or text aswell.
    ui.update_selectize(
        "samp_selection", choices=samp_choices(), selected=samp_ref_list()
    )
    previous = "sample"
    sample_hidden_list = [
        "Materials",
        "Gonio. radius",
        "FreePrm1",
        "FreePrm2",
        "FreePrm3",
        "ranId",
        "Time",
        "Thick",
        "Constrast",
        "Trans",
        "SlitLen",
        "Shift",
        "Transparency",
        "Temperature",
        "Pressure",
        "Omega",
        "Chi",
        "Phi",
        "Azimuth",
    ]
    sample_UI_list = []
    for param, val in sample_params().items():
        if param not in sample_hidden_list:
            if isinstance(val, list):
                if isinstance(val[0], float):
                    ui.insert_ui(
                        ui.input_numeric(id=param, label=param, value=val[0]),
                        selector="#" + previous,
                        where="afterEnd",
                    )
                    sample_UI_list.append(param)
                    previous = param

            if isinstance(val, float):
                ui.insert_ui(
                    ui.input_numeric(id=param, label=param, value=val),
                    selector="#" + previous,
                    where="afterEnd",
                )
                sample_UI_list.append(param)
                previous = param

            if param == "InstrName":
                ui.insert_ui(
                    ui.input_text(id=param, label="Instrument Name", value=val),
                    selector="#" + previous,
                    where="afterEnd",
                )
                sample_UI_list.append(param)
                previous = param

            if param == "Type":
                ui.insert_ui(
                    ui.input_select(
                        id=param,
                        label="Type:",
                        choices={
                            "Debye-Scherrer": "Debye-Scherrer",
                            "Bragg-Brentano": "Bragg-Brentano",
                        },
                        selected=val,
                    ),
                    selector="#" + previous,
                    where="afterEnd",
                )
                sample_UI_list.append(param)
                previous = param
    samp_UI_list.set(sample_UI_list)


def remove_samp_inputs() -> None:
    if sample_params() is not None:
        for param in sample_params().keys():
            ui.remove_ui(selector="div:has(> " + "#" + param + ")")


def remove_inst_inputs() -> None:
    if inst_params() is not None:
        for param in inst_params().keys():
            ui.remove_ui(selector="div:has(> " + "#" + param + ")")


def view_hist() -> None:
    # view a specific subtree of the histogram in the histogram tab
    print("select_view_hist()")


def load_histogram(hist_name: str) -> None:
    """
    loads the selected histogram and updates the UI
    to reflect the new hsitograms data.
    """
    # load the ui for hist data in the project tab
    if hist_name != "init":
        # update the histogram 'data tree' in the sidebar
        h = gpx().histogram(hist_name)
        data: dict = h.data
        options = {}
        for subheading in data:
            options[subheading] = subheading
        select_view_hist.set(options)
        ui.update_select("view_hist_data", choices=select_view_hist())
        # delete old ui
        remove_inst_inputs()
        remove_samp_inputs()
        # set the new histogram parameters for the UI
        # add flag choices dicts here
        hp = load_histogram_parameters(gpx(), hist_name)
        inst_ref_list.set(hp[0])
        inst_params.set(hp[1])
        inst_choices.set(hp[2])
        samp_ref_list.set(hp[3])
        sample_params.set(hp[4])
        samp_choices.set(hp[5])
        # change how parameters are loaded

        # update the plots and the UI
        update_plot(gpx(), hist_name)

        lim_min: float = min(x())
        lim_max: float = max(x())
        lim_low: float = h.Limits("lower")
        lim_up: float = h.Limits("upper")
        ui.update_slider("limits", min=lim_min, max=lim_max, value=[lim_low, lim_up])

        # build the new UI
        build_samp_page()
        build_inst_page()
        build_bkg_page(hist_name)


def update_plot(gpx: GSAS2Project, hist_name: str) -> None:
    """
    updates plot parameters for the powder hsitogram to ensure the
    output is not stale
    """
    tx, ty, tycalc, tdy, tbkg = hist_export(gpx, hist_name)
    x.set(tx)
    y.set(ty)
    ycalc.set(tycalc)
    dy.set(tdy)
    bkg.set(tbkg)


def load_phase() -> None:
    # load the ui for phase data in the project tab TBC or unecessary
    print("select_phase_choices()")


def set_hist_limits(hist_name: str, limits: list) -> None:
    h = gpx().histogram(hist_name)
    h.Limits("lower", limits[0])
    h.Limits("upper", limits[1])


def plot_powder(hist_name: str, limits: list):
    """
    plots the powder histogram data from the current project
    """
    update_plot(gpx(), hist_name)
    pwdr_data = {
        "2 Theta": x(),
        "intensity": y(),
        "fit": ycalc(),
        "background": bkg(),
    }
    df = pd.DataFrame(pwdr_data)
    tdf = pd.DataFrame([[0, 0]], columns=["2 Theta", "intensity"])

    fig = px.scatter(tdf, x="2 Theta", y="intensity", opacity=0, title=hist_name)

    fig.add_scatter(
        x=df["2 Theta"],
        y=df["intensity"],
        mode="markers",
        opacity=0.8,
        name="powder data",
        zorder=0,
    )
    fig.update_traces(
        marker=dict(
            size=5,
            symbol="cross-thin",
            color="royalblue",
            line=dict(
                width=2,
                color="royalblue",
            ),
        ),
        selector=dict(mode="markers"),
    )

    fig.add_scatter(
        x=df["2 Theta"], y=df["fit"], mode="lines", opacity=1, name="fit", zorder=2
    )
    fig.add_scatter(
        x=df["2 Theta"],
        y=df["background"],
        mode="lines",
        opacity=1,
        name="background",
        zorder=1,
    )

    fig.add_vline(x=limits[0], line_width=3, line_dash="dash", line_color="green")
    fig.add_vline(x=limits[1], line_width=3, line_dash="dash", line_color="green")
    # fig.show()
    return fig


def update_history() -> None:
    """
    fetches history from galaxy to populate load project choices.
    uses pandas dataframes for shiny output rendering.
    """
    print("update_history triggered")
    history = gxhistory.gx_update_history()
    hist_frame: pd.DataFrame = pd.DataFrame(history)
    hist_table = hist_frame[["hid", "name", "id"]]
    hist_data.set(hist_table)
    gpx_df = hist_table[hist_table["name"].str.endswith("gpx")]
    gpx_choice_dict = dict(
        [
            (i, str(h) + ": " + fn)
            for i, h, fn in zip(gpx_df["id"], gpx_df["hid"], gpx_df["name"])
        ]
    )

    gpx_choice_dict = dict(reversed(gpx_choice_dict.items()))
    # gpx_choice_dict = {}
    # for row in hist_table.itertuples():
    #    gpx_choice_dict[row.id] = row.hid + ": " + row.name

    select_gpx_choices.set(gpx_choice_dict)  # dictionary with {ID:name}
    ui.update_select("select_gpx", choices=select_gpx_choices())


def view_proj() -> None:
    # view project data window TBC
    print("view_proj_choices")


def load_project(id: str) -> None:
    if id != "init":
        # remove any dynamic UI items from previous project
        remove_inst_inputs()
        remove_samp_inputs()

        # get the file from galaxy and load the gsas project
        hid_and_fn: str = select_gpx_choices()[id]
        fn: str = hid_and_fn.split(": ")[1]

        location: str = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.get_project(id, fp)
        tgpx: GSAS2Project = gsas_load_gpx(fp, fn)
        og_tgpx: GSAS2Project = gsas_load_gpx(fp, "og_" + fn)
        current_gpx_id.set(id)
        current_gpx_fname.set(fn)
        # load the phase names for the sidebar selection
        phase_names = {}
        for phase in tgpx.phases():
            name = phase.name
            phase_names[name] = name
        select_phase_choices.set(phase_names)

        # load the histogram names for sidebar selection
        hist_names = {}
        for hist in tgpx.histograms():
            hist_names[hist.name] = hist.name
        select_hist_choices.set(hist_names)

        # set reactive variable values
        input_gpx_file.set(fp)
        gpx.set(tgpx)
        og_gpx.set(og_tgpx)
        constraints.set([])

        # update the phase/histogram selection uis
        ui.update_select("select_hist", choices=select_hist_choices())
        ui.update_select("select_phase", choices=select_phase_choices())

        # load data for a histogram/clear previous histogram data
        load_histogram(list(hist_names.keys())[0])


def save_inst_params(app_input) -> None:
    """
    collects instrument parameter inputs and saves them to gpx
    """
    # change this to change the full dictionary directly
    # some inputs filtered out so need a reference for which inputs to take
    hist_name: str = app_input.select_hist()
    h = gpx().histogram(hist_name)
    inst_dict_full: dict = h.getHistEntryValue(["Instrument Parameters"])
    irl: list = app_input.inst_selection()
    ip: dict = inst_params().copy()

    # set all flags to false
    for param in ip:
        if isinstance(ip[param], list):
            if len(ip[param]) == 3:
                if ip[param][2]:
                    inst_dict_full[0][param][2] = False

    # add new refinement flags

    inst_ref_dict = {"Instrument Parameters": irl}
    h.set_refinements(inst_ref_dict)

    for param in irl:
        inst_dict_full[0][param][2] = True

    # add new set values
    for param in ip:
        if isinstance(ip[param], list):
            if isinstance(ip[param][0], float) or isinstance(ip[param][1], float):
                if param != "Polariz." and param != "SH/L":
                    inst_dict_full[0][param][1] = getattr(app_input, param)()

    h.setHistEntryValue(["Instrument Parameters"], inst_dict_full)
    inst_params.set(ip)
    inst_ref_list.set(irl)


def save_samp_params(app_input) -> None:
    """
    collects sample parameter inputs and saves them to gpx
    """
    hist_name: str = app_input.select_hist()
    h = gpx().histogram(hist_name)
    sp: dict = sample_params().copy()

    # gets sample refinement input
    srl: list = app_input.samp_selection()

    # set all flags to false
    for param in sp:
        if isinstance(sp[param], list):
            if sp[param][1]:
                sp[param][1] = False

    # set the new chosen flags

    for param in srl:
        sp[param][1] = True

    # set the new values
    for param in sp:
        if param in samp_UI_list():

            if isinstance(sp[param], list):
                sp[param][0] = getattr(app_input, param)()
                print("a")
            elif param == "Type":
                sp[param] = getattr(app_input, param)()
            else:
                print("b")
                sp[param] = getattr(app_input, param)()

            h.setHistEntryValue(["Sample Parameters", param], sp[param])

    # update the reactive values / global values
    samp_ref_list.set(srl)
    sample_params.set(sp)


def submit_out() -> None:
    """
    saves project changes to file and submits to galaxy history
    runs static tool GSAS2_refinement_executor in the background
    loads the refined file back into the interactive tool on completion
    """
    gpx().save()
    save_delta()
    gxhistory.put("delta1")

    # wait for the file to save in galaxy and run refinement
    id = refresh_gpx_history()
    gxhistory.run_refinement(current_gpx_id(), id)
    # current_gpx_id.set(id)

    # wait for refinement to complete
    id = refresh_gpx_history()
    gxhistory.wait_for_dataset(id)

    # load the history with the new refinement output gpx file
    update_history()
    gpx_table: pd.DataFrame = hist_data()[(hist_data()["name"].str.contains("gpx"))]
    row_id: int = gpx_table["hid"].idxmax()
    id: str = gpx_table.loc[row_id, "id"]

    # load the refined output project and update the UI
    load_project(id)
    ui.update_select("select_gpx", selected=id)


def refresh_gpx_history() -> str:
    """Finds the API id of the latest files in the galaxy history.

    Returns:
        str: Galaxy API ID for the msot recent event in the history.
    """
    time.sleep(2)
    update_history()
    row_id: int = hist_data()["hid"].idxmax()
    id: str = hist_data().loc[row_id, "id"]
    return id


def save_delta() -> None:
    diff = DeepDiff(og_gpx(), gpx(), exclude_paths="filename")
    delta = Delta(diff)
    with open("delta1", "wb") as dump_file:
        delta.dump(dump_file)
