from shiny.express import ui
from shiny import reactive
import pandas as pd
import gxhistory
import os
from gsasIImodel import (
    hist_export,
    gsas_load_gpx,
    load_phase_constraints,
    load_histogram_parameters,
)
import matplotlib.pyplot as plt
import typing

"""contains all reactive events functions and variables
and processes all logic from the ui, GSASII and galaxy history models.
note functions defined here cannot directly access inputs from view.
these have to be passed as inputs to the function."""

# reactive value parameters for anything that needs to be passed on
# as a side effect from reactive functions
gpx = reactive.value()
instreflist = reactive.value()
instparams = reactive.value(None)
sampreflist = reactive.value()
sampleparams = reactive.value(None)
inputgpxfile = reactive.value()
instchoices = reactive.value()
sampchoices = reactive.value()
sampUIlist = reactive.value([])

x = reactive.value()
y = reactive.value()
ycalc = reactive.value()
dy = reactive.value()
bkg = reactive.value()

histdata = reactive.value()
constraints = reactive.value()

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


def showphaseconstr():
    """
    TBC reads constraint data from the gpx and re arranges them for UI output
    """
    constraints = load_phase_constraints(gpx())
    # rearrange the data for visualisation
    return constraints


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
    sample_hidden_list = ["Materials", "Gonio. radius", "FreePrm1", "FreePrm2",
                          "FreePrm3", "ranId", "Time",
                          "Thick", "Constrast",
                          "Trans", "SlitLen", "Shift", "Transparency",
                          "Temperature", "Pressure",
                          "Omega", "Chi", "Phi",
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


def update_hist_samp_ui():
    """
    update sample parameters UI elements with data
    from the last selected histogram
    """
    ui.update_selectize("samp_selection", selected=sampreflist())
    for param, val in sampleparams().items():
        ui.update_numeric(param, value=val[0])


def update_hist_inst_ui():
    """
    update instrument parameters UI elements with data
    from the last selected histogram
    """
    ui.update_selectize("inst_selection", selected=instreflist())
    for param, val in instparams().items():
        ui.update_numeric(param, value=val[1])


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
    plt.scatter(x(), y(), c="blue")
    plt.plot(x(), ycalc(), c="green")
    plt.plot(x(), bkg(), c="red")
    plt.title("Powder histogram")
    plt.xlabel("2 Theta")
    plt.ylabel("intensity")


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
    choicedict = dict([(i, fn) for i, fn in zip(histtable["id"], histtable["name"])])
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
        fn = select_gpx_choices()[id]
        location = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.getproject(id, fp)
        tgpx = gsas_load_gpx(fp)

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
        constraints.set([])

        # update the phase/histogram selection uis
        ui.update_select("selecthist", choices=select_hist_choices())
        ui.update_select("selectphase", choices=select_phase_choices())

        # load data for a histogram/clear previous histogram data
        loadhist(list(histnames.keys())[0])

    """def save_inst_params(app_input):

    collects instrument parameter inputs and saves them to gpx

    histname = app_input.selecthist()
    h = gpx().histogram(histname)
    # copies current full instrument parameter dictionary
    # this is actually a list. [0] has the dict
    # [1] has a depracated GSAS1 thing
    instdictfull = h.getHistEntryValue(["Instrument Parameters"])

    # set refinement flags
    irl = app_input.inst_selection()

    # copies instrument  parameters to avoid overwriting the underlying object
    ip = instparams().copy()
    instrefdict = {"Instrument Parameters": irl}
    h.set_refinements(instrefdict)

    # set the refinement flags directly in the dictionary too, so they show up
    # if reloading the project file when no rfinement ahve run
    for param in irl:
        ip[param][2] = True

    # just edit this to add validation for the types

    # update the new parameter values
    for param in ip:
        ip[param][1] = getattr(app_input, param)()
        instdictfull[0][param] = ip[param]

    # copy the new dictionary back into the gpx histogram object
    h.setHistEntryValue(["Instrument Parameters"], instdictfull)

    # set the new values for global reactive variables.
    instreflist.set(irl)
    instparams.set(ip)"""


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

    """def save_samp_params(app_input):

    histname = app_input.selecthist()
    h = gpx().histogram(histname)

    # gets sample refinement input
    srl = app_input.samp_selection()

    # copies sample parameters to avoid overwriting the underlying object
    sp = sampleparams().copy()
    # set the refinement flag in the dictionary itself
    for param in srl:
        sp[param][1] = True

    # add validation here for different params

    # set the new values in the gpx object
    for param in sp:
        sp[param][0] = getattr(app_input, param)()
        h.setHistEntryValue(['Sample Parameters', param], sp[param])

    # update the reactive values / global values
    sampreflist.set(srl)
    sampleparams.set(sp)"""


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
    """
    gpx().save()
    gxhistory.put("output.gpx")