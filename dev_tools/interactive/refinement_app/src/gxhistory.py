from bioblend.galaxy import GalaxyInstance
import logging
import os

"""These functions were edited from the interactive wallace too repo.
Some may not be necessary and anything here should probably be referenced?
"""

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
logging.getLogger("bioblend").setLevel(logging.CRITICAL)
log = logging.getLogger()


def get_galaxy_connection(history_id=None, obj=True):
    # history_id = history_id or os.environ['HISTORY_ID']
    key = os.environ["API_KEY"]
    url = os.environ["GALAXY_URL"]
    gi = GalaxyInstance(url=url, key=key)
    # gi.histories.get_histories(history_id)
    return gi


def put(filename, file_type="auto", history_id=None):
    """
    Given a filename of any file accessible to the docker instance, this
    function will upload that file to galaxy using the current history.
    Does not return anything.
    """

    gi = get_galaxy_connection(history_id=history_id)
    history_id = os.environ["HISTORY_ID"]
    log.debug(
        "Uploading gx=%s history=%s localpath=%s ft=%s",
        gi,
        history_id,
        filename,
        file_type,
    )

    gi.tools.upload_file(filename, history_id)


def updateHist():
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection(history_id=history_id)
    history = gi.histories.show_history(
        history_id=history_id,
        contents=True,
        deleted=False,
        visible=True,
        types=["dataset"],
        keys=["Id", "Hid", "Name"],
    )
    return history


def getproject(dataset_id, filep):
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection(history_id=history_id)
    gi.datasets.download_dataset(
        dataset_id=dataset_id, file_path=filep, use_default_filename=False
    )


def run_refinement(dataset_id, delta_id):
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection(history_id=history_id)
    gi.datasets.wait_for_dataset(delta_id)
    inputdata = {}
    inputdata["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
    inputdata["delta"] = {"values": [{"src": "hda", "id": delta_id}]}
    gi.tools.run_tool(history_id, "gpx_gsas2", inputdata)


def wait_for_dataset(dataset_id):
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection(history_id=history_id)
    gi.datasets.wait_for_dataset(dataset_id)
