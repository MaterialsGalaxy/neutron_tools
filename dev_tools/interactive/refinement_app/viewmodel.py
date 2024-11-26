# contains all reactive events functions and variables
# and processes all logic from the ui, GSASII and galaxy history models.
# note functions defined here cannot directly access inputs from view.
# these have to be passed as inputs to the function.
from shiny.express import ui
from shiny import reactive
import gxhistory
import os
from gsasIImodel import (
    saveParameters,
    hist_export,
    gsas_load_gpx,
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

gpx_choices = {"init":
               "update the history before loading a new project"}
select_gpx_choices = reactive.value(gpx_choices)


def plot_powder():
    plt.scatter(x(), y(), c='blue')
    plt.plot(x(), ycalc(), c='green')
    plt.plot(x(), bkg(), c='red')
    plt.title("Powder histogram")
    plt.xlabel("2 Theta")
    plt.ylabel("intensity")


def updatehistory():
    print("updatehistory triggered")
    histtable = gxhistory.updateHist()
    histdata.set(histtable)
    choicedict = dict([(i, fn) for i, fn in zip(histtable['id'],
                                                histtable['name'])])
    select_gpx_choices.set(choicedict)  # dictionary with {ID:name}
    ui.update_select("selectgpx", choices=select_gpx_choices())


def loadproject(id):
    if id != "init":
        fn = select_gpx_choices()[id]
        location = "/var/shiny-server/shiny_test/work/"
        fp = os.path.join(location, fn)
        gxhistory.getproject(id, fp)
        tgpx, irl, ip, srl, sp = gsas_load_gpx(fp)
        gpx.set(tgpx)
        instreflist.set(irl)
        instparams.set(ip)
        sampreflist.set(srl)
        sampleparams.set(sp)
        inputgpxfile.set(fp)
        tx, ty, tycalc, tdy, tbkg = hist_export(gpx())
        x.set(tx)
        y.set(ty)
        ycalc.set(tycalc)
        dy.set(tdy)
        bkg.set(tbkg)
        update_gpx_ui()


def update_gpx_ui():
    ui.update_selectize("inst_selection", selected=instreflist())
    ui.update_selectize("samp_selection", selected=sampreflist())
    for param, val in instparams().items():
        ui.update_numeric(param, value=val[1])
    for param, val in sampleparams().items():
        ui.update_numeric(param, value=val[0])


def submitout(app_input):
    # collect inputs and add them to the model
    srl = app_input.samp_selection()
    irl = app_input.inst_selection()
    sp = sampleparams().copy()
    ip = instparams().copy()
    for param in sp:
        sp[param][0] = getattr(app_input, param)()
    for param in ip:
        ip[param][1] = getattr(app_input, param)()
    sampreflist.set(srl)
    instreflist.set(irl)
    sampleparams.set(sp)
    instparams.set(ip)
    # save the parameters to the GSAS project file
    # and submit to galaxy history
    saveParameters(gpx(), instreflist(), instparams(),
                   sampreflist(), sampleparams())
    gxhistory.put("output.gpx")


def submit_message():
    result = "Refining sample parameters: {sref} \n\
             with values {svals} \n\
             Refining instrument parameters {iref} \n\
             with values is {ivals}"\
            .format(sref=sampreflist(), svals=sampleparams(),
                    iref=instreflist(), ivals=instparams())
    return result
