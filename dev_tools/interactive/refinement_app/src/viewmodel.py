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
instreflist = reactive.value()
instparams = reactive.value(None)
sampreflist = reactive.value()
sampleparams = reactive.value(None)
inputgpxfile = reactive.value()
instchoices = reactive.value()
sampchoices = reactive.value()
sampUIlist = reactive.value([])

num_bkg_coefs = reactive.value()
current_bkg_func = reactive.value()

x = reactive.value()
y = reactive.value()
ycalc = reactive.value()
dy = reactive.value()
bkg = reactive.value()

histdata = reactive.value()
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


def updatenav(tab):
    """
    updates the tab viewed in the UI.
    The main UI uses a hidden navset so the menus
    can be navigated using the sidebar

    """
    # set the tab in the main view from the sidebar controls
    ui.update_navs(id="tab", selected=tab)


def add_constr(ctype, df):
    """
    wrapper function for adding equivalence or equation constraints
    equation constraints are forced to have a total of 1
    """
    # add constraints to constraints list and to gpx
    constr_vars = df["code"].tolist()
    constr_coefs = df["coefficients"].tolist()
    if ctype == "eqv":
        constraints().append(["EQUIV", constr_vars, constr_coefs])
        gpx().add_EquivConstr(constr_vars, multlist=constr_coefs)
    elif ctype == "eqn":
        constraints().append(["CONST", constr_vars, constr_coefs])
        gpx().add_EqnConstr(1, constr_vars, multlist=constr_coefs)


def build_constraints_df(phasename):
    """
    builds/populates the Dataframe of possible parameters
    to choose for phase constraints
    used so users can make selections for constraint inputs
    """
    # initialise constraints
    constraint_cols = ["code", "phase", "parameter", "atom"]
    phase_constr_df = pd.DataFrame(columns=constraint_cols)

    phase = gpx().phase(phasename)

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
            constraint_vals = [code, phasename, param, atom.label]
            constraint_record = dict(zip(constraint_cols, constraint_vals))
            phase_constr_df = phase_constr_df._append(
                constraint_record, ignore_index=True
            )
    return phase_constr_df


def remove_constraint(id):
    constraints = load_phase_constraints(gpx())
    if isinstance(id, int) and id < len(constraints):
        constraints.pop(id)


def showphaseconstr():
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
                    var_name = var_obj.varname()
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


def saveatomtable(df, phasename):
    """
    saves the edited atom dataframe
    currently only saves refinement flag edits to the gpx
    """

    phase = gpx().phase(phasename)
    for atom in phase.atoms():
        atomrecord = df.loc[df["Name"] == atom.label]
        atom.refinement_flags = atomrecord.iloc[0]["refine"]


def atomdata(phasename):
    """
    generates a pandas dataframe containing data for atoms
    in the selected phase.
    used to render in the phase atom UI.
    """
    phase = gpx().phase(phasename)

    # initialise the dataframe
    atomcols = ["Name", "type", "refine", "x", "y", "z", "frac", "multi", "Uiso"]
    atomframe = pd.DataFrame(columns=atomcols)

    # populate the dataframe with data from the project
    for atom in phase.atoms():
        atomvals = [
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
        atomrecord = dict(zip(atomcols, atomvals))
        atomframe = atomframe._append(atomrecord, ignore_index=True)

    return atomframe


def load_bkg_data(histname):
    if histname != "init":
        bkg_data = gpx().histogram(histname).Background
        return bkg_data
    else:
        return None
    # num_bkg_coefs.set()
    # current_bkg_func.set()


def build_bkg_page(histname):
    bkg_data = load_bkg_data(histname)
    ui.update_select("background_function", selected=bkg_data[0][0])
    ui.update_checkbox("bkg_refine", value=bkg_data[0][1])
    ui.update_numeric("num_bkg_coefs", value=bkg_data[0][2])


def set_bkg_func(histname, func):
    if histname != "init":
        bkg_data = load_bkg_data(histname)
        bkg_data[0][0] = func


def set_bkg_refine(histname, flag):
    if histname != "init":
        bkg_data = load_bkg_data(histname)
        bkg_data[0][1] = flag


def set_bkg_coefs(histname, num):
    if histname != "init":
        bkg_data = load_bkg_data(histname)
        bkg_data[0][2] = num
        current_coefs = len(bkg_data[0]) - 3
        if num > current_coefs:
            bkg_data[0] = bkg_data[0] + [np.float64(0.0)] * (num - current_coefs)


def build_bkg_coef_df(histname):
    if histname != "init":
        bkg_data = load_bkg_data(histname)
        coefs = bkg_data[0][3:]
        bkg_coef_df = pd.DataFrame(coefs, columns=["Background Coefficients"])
        return bkg_coef_df


def save_bkg_coefs(histname, coefs):
    if histname != "init":
        bkg_data = load_bkg_data(histname)
        bkg_data[0][3:] = np.float64(coefs)


def buildinstpage():
    """
    in development
    generate the instrument parameter UI dynamically
    needed as Continuous Wave and Time of Flight experiments
    have different parameters
    """
    # update the refinement flags choices too
    # and filter which inputs to show numerically/text
    ui.update_selectize("inst_selection", choices=instchoices(), selected=instreflist())
    # previous = "inst_selection"

    # generate the new UI elements
    # Ideally generate all directly from the gsas histogram object's
    # instrument parameter dictionary
    # finds previous element from selector, inserts new element after it
    # requires removing too, unclear how this works

    previous = "instruments"

    # could make a dictionary of param keys to ui labels

    for param, val in instparams().items():
        if isinstance(val, list):
            if isinstance(val[0], float) or isinstance(val[1], float):
                if param != "SH/L" and param != "Polariz.":

                    ui.insert_ui(
                        ui.input_numeric(id=param, label=param, value=val[1]),
                        selector="#" + previous,
                        where="afterEnd",
                    )
                    previous = param


def buildsamppage():
    # add updating the flag choices and filter which inputs to show
    # numerically or text aswell.
    ui.update_selectize("samp_selection", choices=sampchoices(), selected=sampreflist())
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
    for param, val in sampleparams().items():
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
    sampUIlist.set(sample_UI_list)


def remove_samp_inputs():
    if sampleparams() is not None:
        for param in sampleparams().keys():
            ui.remove_ui(selector="div:has(> " + "#" + param + ")")


def remove_inst_inputs():
    if instparams() is not None:
        for param in instparams().keys():
            ui.remove_ui(selector="div:has(> " + "#" + param + ")")


def viewhist():
    # view a specific subtree of the histogram in the histogram tab
    print(select_view_hist())


def loadhist(histname):
    """
    loads the selected histogram and updates the UI
    to reflect the new hsitograms data.
    """
    # load the ui for hist data in the project tab
    if histname != "init":
        # update the histogram 'data tree' in the sidebar
        data = gpx().histogram(histname).data
        options = {}
        for subheading in data:
            options[subheading] = subheading
        select_view_hist.set(options)
        ui.update_select("viewhistdata", choices=select_view_hist())
        # delete old ui
        remove_inst_inputs()
        remove_samp_inputs()
        # set the new histogram parameters for the UI
        # add flag choices dicts here
        hp = load_histogram_parameters(gpx(), histname)
        instreflist.set(hp[0])
        instparams.set(hp[1])
        instchoices.set(hp[2])
        sampreflist.set(hp[3])
        sampleparams.set(hp[4])
        sampchoices.set(hp[5])
        # change how parameters are loaded

        # update the plots and the UI
        update_plot(gpx(), histname)

        # build the new UI
        buildsamppage()
        buildinstpage()
        build_bkg_page(histname)


def update_plot(gpx, histname):
    """
    updates plot parameters for the powder hsitogram to ensure the
    output is not stale
    """
    tx, ty, tycalc, tdy, tbkg = hist_export(gpx, histname)
    x.set(tx)
    y.set(ty)
    ycalc.set(tycalc)
    dy.set(tdy)
    bkg.set(tbkg)


def loadphase():
    # load the ui for phase data in the project tab TBC or unecessary
    print(select_phase_choices())


def plot_powder(histname):
    """
    plots the powder histogram data from the current project
    """
    update_plot(gpx(), histname)
    pwdr_data = {
        "2 Theta": x(),
        "intensity": y(),
        "fit": ycalc(),
        "background": bkg(),
    }
    df = pd.DataFrame(pwdr_data)
    tdf = pd.DataFrame([[0, 0]], columns=["2 Theta", "intensity"])

    fig = px.scatter(tdf, x="2 Theta", y="intensity", opacity=0, title=histname)

    fig.add_scatter(x=df["2 Theta"], y=df["intensity"], mode="markers", opacity=0.8, name="powder data", zorder=0)
    fig.update_traces(
        marker=dict(
            size=5,
            symbol="cross-thin",
            color="royalblue",
            line=dict(
                width=2,
                color="royalblue",
            )
        ),
        selector=dict(mode="markers"),
    )

    fig.add_scatter(x=df["2 Theta"], y=df["fit"], mode="lines", opacity=1, name="fit", zorder=2)
    fig.add_scatter(x=df["2 Theta"], y=df["background"], mode="lines", opacity=1, name="background", zorder=1)

    # fig.show()
    return fig


def updatehistory():
    """
    fetches history from galaxy to populate load project choices.
    uses pandas dataframes for shiny output rendering.
    """
    print("updatehistory triggered")
    history = gxhistory.updateHist()
    histframe = pd.DataFrame(history)
    histtable = histframe[["hid", "name", "id"]]
    histdata.set(histtable)
    choicedict = dict(
        [
            (i, str(h) + ": " + fn)
            for i, h, fn in zip(histtable["id"], histtable["hid"], histtable["name"])
        ]
    )
    # choicedict = {}
    # for row in histtable.itertuples():
    #    choicedict[row.id] = row.hid + ": " + row.name

    select_gpx_choices.set(choicedict)  # dictionary with {ID:name}
    ui.update_select("selectgpx", choices=select_gpx_choices())


def viewproj():
    # view project data window TBC
    print(view_proj_choices)


def loadproject(id):
    if id != "init":
        # remove any dynamic UI items from previous project
        remove_inst_inputs()
        remove_samp_inputs()

        # get the file from galaxy and load the gsas project
        hid_and_fn = select_gpx_choices()[id]
        fn = hid_and_fn.split(": ")[1]

        location = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.getproject(id, fp)
        tgpx = gsas_load_gpx(fp, fn)
        og_tgpx = gsas_load_gpx(fp, "og_"+fn)
        current_gpx_id.set(id)
        current_gpx_fname.set(fn)
        # load the phase names for the sidebar selection
        phasenames = {}
        for phase in tgpx.phases():
            name = phase.name
            phasenames[name] = name
        select_phase_choices.set(phasenames)

        # load the histogram names for sidebar selection
        histnames = {}
        for hist in tgpx.histograms():
            histnames[hist.name] = hist.name
        select_hist_choices.set(histnames)

        # set reactive variable values
        inputgpxfile.set(fp)
        gpx.set(tgpx)
        og_gpx.set(og_tgpx)
        constraints.set([])

        # update the phase/histogram selection uis
        ui.update_select("selecthist", choices=select_hist_choices())
        ui.update_select("selectphase", choices=select_phase_choices())

        # load data for a histogram/clear previous histogram data
        loadhist(list(histnames.keys())[0])


def save_inst_params(app_input):
    """
    collects instrument parameter inputs and saves them to gpx
    """
    # change this to change the full dictionary directly
    # some inputs filtered out so need a reference for which inputs to take
    histname = app_input.selecthist()
    h = gpx().histogram(histname)
    instdictfull = h.getHistEntryValue(["Instrument Parameters"])
    irl = app_input.inst_selection()
    ip = instparams().copy()

    # set all flags to false
    for param in ip:
        if isinstance(ip[param], list):
            if len(ip[param]) == 3:
                if ip[param][2]:
                    instdictfull[0][param][2] = False

    # add new refinement flags

    instrefdict = {"Instrument Parameters": irl}
    h.set_refinements(instrefdict)

    for param in irl:
        instdictfull[0][param][2] = True

    # add new set values
    for param in ip:
        if isinstance(ip[param], list):
            if isinstance(ip[param][0], float) or isinstance(ip[param][1], float):
                if param != "Polariz." and param != "SH/L":
                    instdictfull[0][param][1] = getattr(app_input, param)()

    h.setHistEntryValue(["Instrument Parameters"], instdictfull)
    instparams.set(ip)
    instreflist.set(irl)


def save_samp_params(app_input):
    """
    collects sample parameter inputs and saves them to gpx
    """
    histname = app_input.selecthist()
    h = gpx().histogram(histname)
    sp = sampleparams().copy()

    # gets sample refinement input
    srl = app_input.samp_selection()

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
        if param in sampUIlist():

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
    sampreflist.set(srl)
    sampleparams.set(sp)


def submitout():
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
    updatehistory()
    gpx_table = histdata()[(histdata()["name"].str.contains("gpx"))]
    row_id = gpx_table["hid"].idxmax()
    id = gpx_table.loc[row_id, "id"]

    # load the refined output project and update the UI
    loadproject(id)
    ui.update_select("selectgpx", selected=id)


def refresh_gpx_history():
    """Finds the API id of the latest files in the galaxy history.

    Returns:
        str: Galaxy API ID for the msot recent event in the history.
    """
    time.sleep(2)
    updatehistory()
    row_id = histdata()["hid"].idxmax()
    id = histdata().loc[row_id, "id"]
    return id


def save_delta():
    diff = DeepDiff(og_gpx(), gpx(), exclude_paths="filename")
    delta = Delta(diff)
    with open('delta1', 'wb') as dump_file:
        delta.dump(dump_file)
