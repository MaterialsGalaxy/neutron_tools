import matplotlib.pyplot as plt
# import numpy as np
from shiny.express import ui, input
from shiny import reactive, render
# import sys
import os
from gsasIImodel import (
    saveParameters,
    hist_export,
    gsas_load_gpx,
)
import gxhistory

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


ui.page_opts(title="GSASII refinement: instrument parameters", fillable=True)

with ui.navset_card_pill(id="tab"):
    with ui.nav_panel("powder data"):

        @render.plot(alt="A histogram")
        @reactive.event(input.loadgpx)
        def plot():
            plt.scatter(x(), y(), c='blue')
            plt.plot(x(), ycalc(), c='green')
            plt.plot(x(), bkg(), c='red')
            plt.title("Powder histogram")
            plt.xlabel("2 Theta")
            plt.ylabel("intensity")

    with ui.nav_panel("B"):
        ui.input_action_button("updatehist", "update history")


        @render.data_frame
        @reactive.event(input.updatehist)
        def renderupdatehistory():
            return render.DataTable(histdata())


        @reactive.effect
        @reactive.event(input.updatehist)
        def updatehistory():
            histtable = gxhistory.updateHist()
            histdata.set(histtable)
            choicedict = dict([(i, fn) for i, fn in zip(histtable['id'],
                                                        histtable['name'])])
            select_gpx_choices.set(choicedict)  # dictionary with {ID:name}
            ui.update_select("selectgpx", choices=select_gpx_choices())

        histdata = reactive.value()
        gpx_choices = {"init":
                       "update the history before loading a new project"}
        select_gpx_choices = reactive.value(gpx_choices)

        ui.input_select("selectgpx", "load GSASII project:", gpx_choices)
        ui.input_action_button("loadgpx", "Load project")


        @reactive.effect
        @reactive.event(input.loadgpx)
        def loadproject():
            if input.selectgpx() != "init":
                fn = select_gpx_choices()[input.selectgpx()]
                location = "/var/shiny-server/shiny_test/work/"
                fp = os.path.join(location, fn)
                gxhistory.getproject(input.selectgpx(), fp)
                # gsasIImodel.loadgpx(fp) load gxp into ui
                irl, ip, srl, sp = gsas_load_gpx(fp)
                instreflist.set(irl)
                instparams.set(ip)
                sampreflist.set(srl)
                sampleparams.set(sp)
                inputgpxfile.set(fp)

                tx, ty, tycalc, tdy, tbkg = hist_export(inputgpxfile())
                x.set(tx)
                y.set(ty)
                ycalc.set(tycalc)
                dy.set(tdy)
                bkg.set(tbkg)

                ui.update_selectize("inst_selection", selected=instreflist())
                ui.update_selectize("samp_selection", selected=instreflist())

                ui.update_numeric("Lam", value=instparams()["Lam"][0])
                ui.update_numeric("Zero", value=instparams()["Zero"][0])
                ui.update_numeric("U", value=instparams()["U"][0])
                ui.update_numeric("V", value=instparams()["V"][0])
                ui.update_numeric("W", value=instparams()["W"][0])
                ui.update_numeric("X", value=instparams()["X"][0])
                ui.update_numeric("Y", value=instparams()["Y"][0])
                ui.update_numeric("Z", value=instparams()["Z"][0])

                ui.update_numeric("Scale", value=sampleparams()["Scale"][0])
                ui.update_numeric("DisplaceX",
                                  value=sampleparams()["DisplaceX"][0])
                ui.update_numeric("DisplaceY",
                                  value=sampleparams()["DisplaceY"][0])
                ui.update_numeric("Absorption",
                                  value=sampleparams()["Absorption"][0])



    with ui.nav_panel("C"):
        "Panel C content"

    with ui.nav_menu("Other links"):
        with ui.nav_panel("D"):
            "Page D content"

        "----"
        "Description:"
        with ui.nav_control():
            ui.a("Shiny", href="https://shiny.posit.co", target="_blank")


with ui.sidebar(bg="#f8f8f8", position='left'):
    ui.input_selectize(
        "inst_selection",
        "Select instrument parameters to refine:",
        {"Lam": "Lam", "Zero": "Zero", "U": "U", "V": "V", "W": "W",
         "X": "X", "Y": "Y", "Z": "Z"},
        multiple=True,
        selected=None,
    )

    ui.input_numeric("Lam", "Lam", 0)
    ui.input_numeric("Zero", "Zero", 0)
    ui.input_numeric("U", "U", 0)
    ui.input_numeric("V", "V", 0)
    ui.input_numeric("W", "W", 0)
    ui.input_numeric("X", "X", 0)
    ui.input_numeric("Y", "Y", 0)
    ui.input_numeric("Z", "Z", 0)
    # ui.input_numeric("SHL", "SH/L", instparams["SH/L"][0])

    ui.input_selectize(
        "samp_selection",
        "Select sample parameters to refine:",
        {"Scale": "Scale", "DisplaceX": "Sample X displ. perp. to beam",
            "DisplaceY": "Sample Y displ. prll. to beam",
            "Absorption": "Sample Absorption"},
        multiple=True,
        selected=None,
    )

    ui.input_numeric("Scale", "histogram scale factor",
                     0)
    ui.input_numeric("DisplaceX", "Sample X displ. perp. to beam",
                     0)
    ui.input_numeric("DisplaceY", "Sample Y displ. prll. to beam",
                     0)
    ui.input_numeric("Absorption", "Sample Absorption",
                     0)

    ui.input_action_button("submit", "submit")

    @reactive.effect
    @reactive.event(input.submit)
    def submitout():

        # collect inputs and add them to the model

        sampreflist.set(input.samp_selection())
        instreflist.set(input.inst_selection())
        sp = sampleparams().copy()
        ip = instparams().copy()

        for param in sp:
            sp[param][0] = getattr(input, param)()

        for param in ip:
            ip[param][1] = getattr(input, param)()

        sampleparams.set(sp)
        instparams.set(ip)

        # save the parameters to the GSAS project file
        # and submit to galaxy history

        saveParameters("output.gpx", instreflist(), instparams(),
                       sampreflist(), sampleparams())
        gxhistory.put("output.gpx")


    @render.text
    @reactive.event(input.submit)
    def submit_text():
        # print out the new refinement parameters

        result = "Refining sample parameters: {sref} \n\
                with values {svals} \n\
                Refining instrument parameters {iref} \n\
                with values is {ivals}"\
                .format(sref=sampreflist(), svals=sampleparams(),
                        iref=instreflist(), ivals=instparams())
        return result
