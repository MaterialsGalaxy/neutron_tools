# contains all reactive events functions and variables
# and processes all logic from the ui, GSASII and galaxy history models.
# note functions defined here cannot directly access inputs from view.
# these have to be passed as inputs to the function.
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

gpx = reactive.value()
instreflist = reactive.value()
instparams = reactive.value()
sampreflist = reactive.value()
sampleparams = reactive.value()
inputgpxfile = reactive.value()

x = reactive.value()
y = reactive.value()
ycalc = reactive.value()
dy = reactive.value()
bkg = reactive.value()

histdata = reactive.value()
constraints = reactive.value()

gpx_choices = {"init":
               "update the history before loading a new project"}
select_gpx_choices = reactive.value(gpx_choices)

phase_choices = {"init":
                 "Load a project before selecting a phase"}
select_phase_choices = reactive.value(phase_choices)

hist_choices = {"init":
                "Load a project before selecting a histogram"}
select_hist_choices = reactive.value(hist_choices)
view_hist_choices = {"init":
                     "Load a project before selecting a histogram"}
select_view_hist = reactive.value(view_hist_choices)

view_proj_choices = {"Notebook": "Notebook", "Controls": "Controls",
                     "Constraints": "Constraints", "Restraints": "Restraints",
                     "Rigid Bodies": "Rigid Bodies"}


def updatenav(tab):
    # set the tab in the main view from the sidebar controls
    ui.update_navs(id="tab", selected=tab)


def add_constr(ctype, df):
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
    constraint_cols = ["code", "phase", "parameter", "atom"]
    phase_constr_df = pd.DataFrame(columns=constraint_cols)
    phase = gpx().phase(phasename)
    parameters = ["Afrac", "AUiso"]
    for param in parameters:
        i = 0
        for atom in phase.atoms():
            code = str(phase.id)+"::"+param+":"+str(i)
            i += 1
            constraint_vals = [code, phasename, param, atom.label]
            constraint_record = dict(zip(constraint_cols, constraint_vals))
            phase_constr_df = phase_constr_df._append(constraint_record,
                                                      ignore_index=True)
    return phase_constr_df


def showphaseconstr():
    constraints = load_phase_constraints(gpx())
    # rearrange the data for visualisation
    return constraints


def saveatomtable(df, phasename):
    # saves the atom table edits from ui input.
    # save to gpx.
    phase = gpx().phase(phasename)
    for atom in phase.atoms():
        atomrecord = df.loc[df['Name'] == atom.label]
        atom.refinement_flags = atomrecord.iloc[0]['refine']


def atomdata(phasename):
    phase = gpx().phase(phasename)
    atomcols = ["Name", "type", "refine", "x", "y", "z",
                "frac", "multi", "Uiso"]
    atomframe = pd.DataFrame(columns=atomcols)
    for atom in phase.atoms():
        atomvals = [atom.label, atom.type, atom.refinement_flags,
                    atom.coordinates[0], atom.coordinates[1],
                    atom.coordinates[2], atom.occupancy, atom.mult, atom.uiso]
        atomrecord = dict(zip(atomcols, atomvals))
        atomframe = atomframe._append(atomrecord, ignore_index=True)
    return atomframe


def buildinstpage():
    # builds the instrument parameter panel
    ui.update_selectize("inst_selection", selected=instreflist())
    previous = "inst_selection"
    for param, val in instparams().items():
        ui.insert_ui(
            ui.input_numeric(param, param, value=val[1]),
            selector="#"+previous,
            where="afterEnd",
        )
        previous = param


def update_hist_samp_ui():
    ui.update_selectize("samp_selection", selected=sampreflist())
    for param, val in sampleparams().items():
        ui.update_numeric(param, value=val[0])


def update_hist_inst_ui():
    ui.update_selectize("inst_selection", selected=instreflist())
    for param, val in instparams().items():
        ui.update_numeric(param, value=val[1])


def viewhist():
    # view a specific subtree of the histogram in the histogram tab
    print(select_view_hist())


def loadhist(histname):
    # load the ui for hist data in the project tab
    # print(select_hist_choices())
    if histname != "init":
        data = gpx().histogram(histname).data
        options = {}
        for subheading in data:
            options[subheading] = subheading
        select_view_hist.set(options)
        ui.update_select("viewhistdata", choices=select_view_hist())

        # code for after histogram selection
        irl, ip, srl, sp = load_histogram_parameters(gpx(), histname)
        # to be put after the histogram is chosen
        instreflist.set(irl)
        instparams.set(ip)
        sampreflist.set(srl)
        sampleparams.set(sp)
        update_plot(gpx(), histname)
        update_hist_samp_ui()
        update_hist_inst_ui()


def update_plot(gpx, histname):
    tx, ty, tycalc, tdy, tbkg = hist_export(gpx, histname)
    x.set(tx)
    y.set(ty)
    ycalc.set(tycalc)
    dy.set(tdy)
    bkg.set(tbkg)


def loadphase():
    # load the ui for phase data in the project tab
    print(select_phase_choices())


def plot_powder(histname):
    update_plot(gpx(), histname)
    plt.scatter(x(), y(), c='blue')
    plt.plot(x(), ycalc(), c='green')
    plt.plot(x(), bkg(), c='red')
    plt.title("Powder histogram")
    plt.xlabel("2 Theta")
    plt.ylabel("intensity")


def updatehistory():
    print("updatehistory triggered")
    history = gxhistory.updateHist()
    histframe = pd.DataFrame(history)
    histtable = histframe[["hid", "name", "id"]]
    histdata.set(histtable)
    choicedict = dict([(i, fn) for i, fn in zip(histtable['id'],
                                                histtable['name'])])
    select_gpx_choices.set(choicedict)  # dictionary with {ID:name}
    ui.update_select("selectgpx", choices=select_gpx_choices())


def viewproj():
    # view project data window
    print(view_proj_choices)


def loadproject(id):
    if id != "init":
        fn = select_gpx_choices()[id]
        location = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.getproject(id, fp)
        tgpx = gsas_load_gpx(fp)
        phasenames = {}
        for phase in tgpx.phases():
            name = phase.name
            phasenames[name] = name
        select_phase_choices.set(phasenames)

        histnames = {}
        for hist in tgpx.histograms():
            histnames[hist.name] = hist.name
        select_hist_choices.set(histnames)

        inputgpxfile.set(fp)
        gpx.set(tgpx)
        constraints.set([])

        ui.update_select("selecthist", choices=select_hist_choices())
        ui.update_select("selectphase", choices=select_phase_choices())
        loadhist(list(histnames.keys())[0])


def save_inst_params(app_input):
    # collects inputs and updates the gpx object
    histname = app_input.selecthist()
    h = gpx().histogram(histname)
    instdictfull = h.getHistEntryValue(['Instrument Parameters'])
    # set refinement flags
    irl = app_input.inst_selection()
    ip = instparams().copy()
    instrefdict = {'Instrument Parameters': irl}
    h.set_refinements(instrefdict)

    for param in irl:
        ip[param][2] = True
    for param in ip:
        ip[param][1] = getattr(app_input, param)()
        instdictfull[0][param] = ip[param]
    h.setHistEntryValue(['Instrument Parameters'],
                        instdictfull)
    instreflist.set(irl)
    instparams.set(ip)


def save_samp_params(app_input):
    # collects inputs and updates the gpx object
    histname = app_input.selecthist()
    h = gpx().histogram(histname)
    srl = app_input.samp_selection()
    sp = sampleparams().copy()
    for param in srl:
        sp[param][1] = True
    sampreflist.set(srl)
    sampleparams.set(sp)
    for param in sp:
        sp[param][0] = getattr(app_input, param)()
        h.setHistEntryValue(['Sample Parameters', param], sp[param])


def submitout():
    gpx().save()
    gxhistory.put("output.gpx")


def submit_message():
    result = "Refining sample parameters: {sref} \n\
             with values {svals} \n\
             Refining instrument parameters {iref} \n\
             with values is {ivals}"\
            .format(sref=sampreflist(), svals=sampleparams(),
                    iref=instreflist(), ivals=instparams())
    return result
