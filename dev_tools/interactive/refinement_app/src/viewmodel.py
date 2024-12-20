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
    GSAS2Project,
)
import plotly.express as px
import typing
import time

"""contains all reactive events functions and variables
and processes all logic from the ui, GSASII and galaxy history models.
note functions defined here cannot directly access inputs from view.
these have to be passed as inputs to the function."""

# store the GSASII project object as a reactive value as it will be
# edited as a side effect by all reactive functions.
gpx = reactive.value()

# initial values for sidebar selections when no project is loaded
# reactive values for when projects are loaded
gpx_choices = {"init": "update the history before loading a new project"}

phase_choices = {"init": "Load a project before selecting a phase"}

hist_choices = {"init": "Load a project before selecting a histogram"}

view_hist_choices = {"init": "Load a project before selecting a histogram"}

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
    """changes the nvaigation tab in the UI

    Args:
        tab (str): the id of the tab to change to
    """
    # set the tab in the main view from the sidebar controls
    ui.update_navs(id="tab", selected=tab)


def add_constr(ctype: str, df: pd.DataFrame, var_df: pd.DataFrame) -> None:
    """adds a valid phase constraint to the GSASII project.

    Args:
        ctype (str): denotes the type of phase constraint
        df (pd.DataFrame): selected constraint parameters and coefficients
        var_df (pd.DataFrame): table of permitted constraint parameters
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
            gpx().add_EquivConstr(constr_vars, multlist=coefs)
        elif ctype == "eqn":
            gpx().add_EqnConstr(1, constr_vars, multlist=coefs)


def build_constraints_df(phase_name: str) -> pd.DataFrame:
    """Builds a Dataframe of variables permitted in a phase constraint.
    It contains variables' codes, phasenames, parameters and atom labels.

    Args:
        phase_name (str): the name of the phase of interest

    Returns:
        pd.DataFrame: The dataframe of variables
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


def remove_constraint(id: int) -> None:
    """removes a phase constraint from the project with the given id

    Args:
        id (str): list index of the selected constraint
        from the list containing all phase constraints
        in the GSASII project object.
    """
    constraints = load_phase_constraints(gpx())
    if isinstance(id, int) and id < len(constraints):
        constraints.pop(id)


def show_phase_constr() -> pd.DataFrame:
    """Reads the current phase constraints from the GSASII project
    and generates a readable table to be output to the UI.

    Returns:
        pd.DataFrame: A table of current phase constraints in the project
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
    """Saves refinement flag settings for the phase atoms from the UI
    to the GSASII project object.

    Args:
        df (pd.DataFrame): The dataframe of the phase atoms
        phase_name (str): the name of the phase edited in the GSASII project
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
    """Generates a dataframe for the atoms in the phase, containing
    the atoms': labels, types, refinement flags, unit cell coordinates,
    site occupation fraction, multiplicity, and atomic displacement.

    Args:
        phase_name (str): name of the phase the atoms belong to

    Returns:
        pd.DataFrame: dataframe for the atoms in the phase
    """
    phase = gpx().phase(phase_name)

    # initialise the dataframe
    atom_cols = ["Name",
                 "type",
                 "refine",
                 "x",
                 "y",
                 "z",
                 "frac",
                 "multi",
                 "Uiso"]
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
    """loads Background data and coefficients
    from the selected histogram in the GSASII project object.

    Args:
        hist_name (str): The name of the selected histogram.

    Returns:
        list[list, dict]: Background parameters with:
        index 0 a list of the background type refinement flags and coefficients
        and index 1 a dictionary relating to additional background peaks.
    """
    if hist_name != "init":
        bkg_data: list[list, dict] = gpx().histogram(hist_name).Background
        return bkg_data
    else:
        return None


def build_bkg_page(hist_name: str) -> None:
    """updates the UI elements for the histogram background.

    Args:
        hist_name (str): name of the histogram which provides the data
    """
    bkg_data = load_bkg_data(hist_name)
    ui.update_select("background_function", selected=bkg_data[0][0])
    ui.update_checkbox("bkg_refine", value=bkg_data[0][1])
    ui.update_numeric("num_bkg_coefs", value=bkg_data[0][2])


def set_bkg_func(hist_name: str, func_name: str) -> None:
    """sets the background function type for the chosen histogram
    in the GSASII project object

    Args:
        hist_name (str): name of the histogram to make changes to
        func_name (str): name of the background function
    """
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][0] = func_name


def set_bkg_refine(hist_name: str, flag: bool) -> None:
    """Sets the refinement flag on or off for the chosen histogram in
    the GSASII project object.

    Args:
        hist_name (str): the name of the histogram being edited
        flag (bool): the value of the refinement flag
    """
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][1] = flag


def set_bkg_coefs(hist_name: str, num_coefs: int) -> None:
    """sets the number of background coefficients for the chosen histogram
    in the GSASII project object

    Args:
        hist_name (str): The name of the histogram being edited
        num_coefs (int): the new number of background coefficients being set
    """
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        bkg_data[0][2] = num_coefs
        current_coefs = len(bkg_data[0]) - 3
        if num_coefs > current_coefs:
            xtra_coefs = num_coefs - current_coefs
            bkg_data[0] = bkg_data[0] + [np.float64(0.0)] * xtra_coefs


def build_bkg_coef_df(hist_name: str) -> pd.DataFrame:
    """generates a dataframe of the current background coefficients
      in the selected histogram from the GSASII project object.

    Args:
        hist_name (str): Name of the histogram being examined

    Returns:
        pd.DataFrame: A table of coefficients to be output to the UI
    """
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        coefs = bkg_data[0][3:]
        bkg_coef_df = pd.DataFrame(coefs, columns=["Background Coefficients"])
        return bkg_coef_df


def save_bkg_coefs(hist_name: str, coefs: list) -> None:
    """Saves a background coefficient list to the selected histogram
    in the GSASII Project.

    Args:
        hist_name (str): name of the histogram being edited
        coefs (list): the new list of background coefficients
    """
    if hist_name != "init":
        bkg_data = load_bkg_data(hist_name)
        try:
            new_coefs = np.float64(coefs)

        except Exception:
            print("invalid coefficient inputs")
        else:
            bkg_data[0][3:] = new_coefs


def build_instrument_df(hist_name) -> pd.DataFrame:
    """Builds a dataframe of instrument parameter values
    taken from the selected GSASII Project object histogram.
    The returned dataframe is used to be output to the UI.

    Args:
        hist_name (_type_): Name of the selected Histogram

    Returns:
        pd.DataFrame: Table of instrument parameter values.
    """
    # get the instrument parameters from the GSASII project object
    h = gpx().histogram(hist_name)
    instrument_parameters: dict = h.getHistEntryValue(["Instrument Parameters"])[0]
    instrument_df = pd.DataFrame(columns=["Parameter", "Value"])

    for param, val in instrument_parameters.items():
        no_input_list = ["Source"]
        if param not in no_input_list:
            if isinstance(val, list):
                df_value = val[1]
            else:
                continue
            new_row = {"Parameter": param, "Value": df_value}
            instrument_df.loc[len(instrument_df)] = new_row

    return instrument_df


def save_instrument_parameters(
    hist_name: str, instrument_df: pd.DataFrame, instrument_refinements: list
) -> None:
    """Saves instrument parameters and refinement parameters
    from an input Dataframe and refinement parameter list
    to the selected histogram in the GSASII Project object.

    Args:
        hist_name (str): The name of the selected histogram.
        instrument_df (pd.DataFrame): The input instrument parameters values.
        instrument_refinements (list): The parameters to be refined.
    """
    h = gpx().histogram(hist_name)
    instrument_parameters = h.getHistEntryValue(["Instrument Parameters"])[0]
    # set all flags to false
    for param, val in instrument_parameters.items():
        if isinstance(val, list) and len(val) == 3:
            if val[2]:
                val[2] = False

    # set the new chosen flags
    for param in instrument_refinements:
        instrument_parameters[param][2] = True

    # copy in parameter values row by row
    for row in instrument_df.itertuples():
        param = row.Parameter
        df_value = row.Value
        val = instrument_parameters[param]

        # type validation
        if isinstance(val, list):
            # set values in GSASII project object directly
            val[1] = type(val[1])(df_value)


def update_instrument_refinements(hist_name: str) -> None:
    """updates the selection box of instrument refinements with
    an updated list of permitted instrument refinement parameters
    and currently applied refinement parameters
    from the selected histogram in the GSASII project object.

    Args:
        hist_name (str): The name of the selected histogram.
    """
    h = gpx().histogram(hist_name)
    instrument_parameters = h.getHistEntryValue(["Instrument Parameters"])[0]

    # populating list of sample refinements that are already active
    instrument_refinement_choices = {}
    instrument_refinements = []
    no_refinements = ["Bank", "Source", "Type"]
    for param, val in instrument_parameters.items():
        # set sample choices dict for UI
        if param not in no_refinements:
            if isinstance(val, list) and len(val) == 3:
                if isinstance(val[1], (int, float)):
                    instrument_refinement_choices[param] = param
                    if val[2]:
                        instrument_refinements.append(param)

    ui.update_selectize(
        "inst_selection",
        choices=instrument_refinement_choices,
        selected=instrument_refinements,
    )


def build_sample_df(hist_name: str) -> pd.DataFrame:
    """Builds a dataframe of the selected histograms Sample Parameters
    to be output to the UI.

    Args:
        hist_name (str): Name of the selected histogram.

    Returns:
        pd.DataFrame: Table of Sample parameter values to be output to the UI.
    """

    # get the sample parameters from the GSASII project object
    h = gpx().histogram(hist_name)
    sample_parameters: dict = h.getHistEntryValue(["Sample Parameters"])
    sample_df = pd.DataFrame(columns=["Parameter", "Value"])

    # populate the dataframe with sample parameters and values
    for param, val in sample_parameters.items():
        no_input_list = ["Materials"]
        if param not in no_input_list:

            if isinstance(val, list):
                df_value = val[0]
            elif isinstance(val, (str, float, int)):
                df_value = val
            else:
                continue

            new_row = {"Parameter": param, "Value": df_value}
            sample_df.loc[len(sample_df)] = new_row

    return sample_df


def save_sample_parameters(
    hist_name: str, sample_df: pd.DataFrame, sample_refinements: list
) -> None:
    """saves sample parameters from an input dataframe
    to the selected histogram in the GSASII project object.

    Args:
        hist_name (str): name of the selected histogram
        sample_df (pd.DataFrame): sample parameter values input from the UI
    """
    h = gpx().histogram(hist_name)
    sample_parameters = h.getHistEntryValue(["Sample Parameters"])

    # set all flags to false
    for param, val in sample_parameters.items():
        if isinstance(val, list):
            if val[1]:
                val[1] = False

    # set the new chosen flags

    for param in sample_refinements:
        sample_parameters[param][1] = True

    # copy in parameter values row by row
    for row in sample_df.itertuples():
        param = row.Parameter
        df_value = row.Value
        val = sample_parameters[param]

        # type validation
        if isinstance(val, list):
            # set values in GSASII project object directly
            val[0] = type(val[0])(df_value)
        else:
            # these parameters have to be set in the project object
            # through the setHistEntryValue method
            h.setHistEntryValue(["Sample Parameters", param],
                                type(val)(df_value))


def update_sample_refinements(hist_name: str) -> None:
    """Updates the selection box of sample refinements with
    an updated list of refineable parameters
    and currently selected parameters
    from the selected histogram in the GSASII project object.

    Args:
        hist_name (str): The name of the selected histogram.
    """
    h = gpx().histogram(hist_name)
    sample_parameters = h.getHistEntryValue(["Sample Parameters"])

    # populating list of sample refinements that are already active
    sample_refinement_choices = {}
    sample_refinements = []
    for param, val in sample_parameters.items():
        # set sample choices dict for UI
        if isinstance(val, list):
            if isinstance(val[1], bool):
                sample_refinement_choices[param] = param
                if val[1]:
                    sample_refinements.append(param)

    # update the UI
    ui.update_selectize(
        "samp_selection",
        choices=sample_refinement_choices,
        selected=sample_refinements,
    )


def load_histogram(hist_name: str) -> None:
    """Loads all data for the UI histogram pages and updates the plots

    Args:
        hist_name (str): name of the selected histogram
    """
    # load the ui for hist data in the project tab
    if hist_name != "init":
        # update the histogram 'data tree' in the sidebar
        h = gpx().histogram(hist_name)
        data: dict = h.data
        options = {}
        for subheading in data:
            options[subheading] = subheading
        ui.update_select("view_hist_data", choices=options)

        # update the plots and the UI
        plot_data = hist_export(gpx(), hist_name)
        lim_min: float = min(plot_data[0])
        lim_max: float = max(plot_data[0])
        lim_low: float = h.Limits("lower")
        lim_up: float = h.Limits("upper")
        ui.update_slider("limits",
                         min=lim_min,
                         max=lim_max,
                         value=[lim_low, lim_up],
                         )

        # build the new UI
        update_sample_refinements(hist_name)
        build_bkg_page(hist_name)
        update_instrument_refinements(hist_name)


def set_hist_limits(hist_name: str, limits: list) -> None:
    """Sets histogram limits overwhich the refinement will be calculated.
    Changes are saved to the GSASII Project object.

    Args:
        hist_name (str): name of the histogram being edited
        limits (list): a list containing the lower and upper limits.
    """
    h = gpx().histogram(hist_name)
    h.Limits("lower", limits[0])
    h.Limits("upper", limits[1])


def plot_powder(hist_name: str, limits: list):
    """generates a plotly express figure for the histogram data
    with the powder data, the fit, the background and the limit lines.
    The figure is used to output a plot to the UI.

    Args:
        hist_name (str): The name of the histogram the figure is made for
        limits (list): a list of the lower and upper limits of the refinement
    Returns:
        _type_: _description_
    """
    x, y, ycalc, dy, bkg = hist_export(gpx(), hist_name)
    pwdr_data = {
        "2 Theta": x,
        "intensity": y,
        "fit": ycalc,
        "background": bkg,
    }
    df = pd.DataFrame(pwdr_data)
    tdf = pd.DataFrame([[0, 0]], columns=["2 Theta", "intensity"])

    fig = px.scatter(tdf,
        x="2 Theta",
        y="intensity",
        opacity=0,
        title=hist_name,
    )

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
        x=df["2 Theta"],
        y=df["fit"],
        mode="lines",
        opacity=1,
        name="fit",
        zorder=2,
    )

    fig.add_scatter(
        x=df["2 Theta"],
        y=df["background"],
        mode="lines",
        opacity=1,
        name="background",
        zorder=1,
    )

    fig.add_vline(
        x=limits[0],
        line_width=3,
        line_dash="dash",
        line_color="green",
    )

    fig.add_vline(
        x=limits[1],
        line_width=3,
        line_dash="dash",
        line_color="green",
    )

    return fig


def get_gpx_choices() -> dict:
    history_table = get_update_history()
    gpx_df = history_table[history_table["name"].str.endswith("gpx")]
    gpx_choice_dict = dict(
        [
            (i, str(h) + ": " + fn)
            for i, h, fn in zip(gpx_df["id"], gpx_df["hid"], gpx_df["name"])
        ]
    )

    gpx_choices = dict(reversed(gpx_choice_dict.items()))
    # gpx_choice_dict = {}
    # for row in history_table.itertuples():
    #    gpx_choice_dict[row.id] = row.hid + ": " + row.name
    return gpx_choices


def get_update_history() -> pd.DataFrame:
    history = gxhistory.gx_update_history()
    history_df: pd.DataFrame = pd.DataFrame(history)
    history_table = history_df[["hid", "name", "id"]]

    return history_table


def update_history() -> None:
    """gets the galaxy history from the galaxy instance
    and generates a history table for the UI ouput.
    This table is set as a reactive variable.
    Also updates the UI choices for projects to load from the galaxy history.
    """
    print("update_history triggered")

    gpx_choices = get_gpx_choices()
    ui.update_select("select_gpx", choices=gpx_choices)


def load_project(id: str) -> None:
    """Loads a GSASII project file from the galaxy history
    using its galaxy API id.
    The file is saved in the interactive tool and
    the other UI pages are updated with
    the new data from the selected project.

    Args:
        id (str): The galaxy API ID of the selected project file.
    """
    if id != "init":

        # get the file from galaxy and load the gsas project
        hid_and_fn: str = get_gpx_choices()[id]
        fn: str = hid_and_fn.split(": ")[1]

        location: str = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.get_project(id, fp)
        tgpx: GSAS2Project = gsas_load_gpx(fp, fn)
        og_tgpx: GSAS2Project = gsas_load_gpx(fp, "og_" + fn)
        # load the phase names for the sidebar selection
        phase_names = {}
        for phase in tgpx.phases():
            name = phase.name
            phase_names[name] = name

        # load the histogram names for sidebar selection
        hist_names = {}
        for hist in tgpx.histograms():
            hist_names[hist.name] = hist.name

        # set reactive variable values
        gpx.set(tgpx)

        # update the phase/histogram selection uis
        ui.update_select("select_hist", choices=hist_names)
        ui.update_select("select_phase", choices=phase_names)

        # load data for a histogram/clear previous histogram data
        load_histogram(list(hist_names.keys())[0])


def submit_out(current_gpx_id) -> None:
    """saves project changes to the .gpx file
    and submits them as a delta file to the galaxy history.
    The static tool GSAS2_refinement_executor then runs in galaxy.
    The refined file is loaded back into the interactive tool on completion.
    """
    
    gpx().save()
    file_path:str = gpx().filename
    file_name = os.path.basename(file_path)
    save_delta(file_name)
    gxhistory.put("delta1")

    # wait for the file to save in galaxy and run refinement
    id = refresh_latest_history_entry_id()
    gxhistory.run_refinement(current_gpx_id, id)
    # current_gpx_id.set(id)

    # wait for refinement to complete
    id = refresh_latest_history_entry_id()
    gxhistory.wait_for_dataset(id)

    # load the history with the new refinement output gpx file
    id:str = list(get_gpx_choices())[0]
    # gpx_table: pd.DataFrame = hist_table[(hist_table["name"].str.contains("gpx"))]
    # row_id: int = gpx_table["hid"].idxmax()
    # id: str = gpx_table.loc[row_id, "id"]

    # load the refined output project and update the UI
    update_history()
    load_project(id)
    ui.update_select("select_gpx", selected=id)


def refresh_latest_history_entry_id() -> str:
    """Finds the API id of the latest files in the galaxy history.

    Returns:
        str: Galaxy API ID for the msot recent entry in the history.
    """
    time.sleep(2)
    hist_table = get_update_history()
    row_id: int = hist_table["hid"].idxmax()
    id: str = hist_table.loc[row_id, "id"]
    return id


def save_delta(file_name: str) -> None:
    """saves the difference between the current project file being edited
    and its original from the galaxy history as a "delta" binary file."""
    og_project_file = "og_" + file_name
    og_gpx = gsas_load_gpx(og_project_file, og_project_file)
    diff = DeepDiff(og_gpx, gpx(), exclude_paths="filename")
    delta = Delta(diff)
    with open("delta1", "wb") as dump_file:
        delta.dump(dump_file)
