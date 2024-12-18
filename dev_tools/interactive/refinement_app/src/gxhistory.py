from bioblend.galaxy import GalaxyInstance
import logging
import os
import typing


DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
logging.getLogger("bioblend").setLevel(logging.CRITICAL)
log = logging.getLogger()


def get_galaxy_connection():
    """connects to a galaxy isntance using the API Key and URL provided in the environment.
    These environement variables are provided to the interactive tool by the galaxy instance
    when the tool is first run.

    Returns:
        _type_: a galaxy instance object which can be used to get a history, upload files to the instance
                and run static tools in galaxy, all from the interactive tool.
    """
    key: str = os.environ["API_KEY"]
    url: str = os.environ["GALAXY_URL"]
    gi = GalaxyInstance(url=url, key=key)
    return gi


def put(file_name: str, file_type: str = "auto") -> None:
    """
    Uploads a file from the interactive tool to the galaxy history.
    Args:
        file_name (str): name of the file to upload
        file_type (str, optional): type of the file to upload. Defaults to "auto".
    """

    gi = get_galaxy_connection()
    history_id = os.environ["HISTORY_ID"]
    log.debug(
        "Uploading gx=%s history=%s localpath=%s ft=%s",
        gi,
        history_id,
        file_name,
        file_type,
    )

    gi.tools.upload_file(file_name, history_id)


def gx_update_history() -> dict:
    """refreshes the entries from the galaxy history and returns them as a dictionary.

    Returns:
        dict: the galaxy history which can be made into a dataframe.
    """
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection()
    history = gi.histories.show_history(
        history_id=history_id,
        contents=True,
        deleted=False,
        visible=True,
        types=["dataset"],
        keys=["Id", "Hid", "Name"],
    )
    return history


def get_project(dataset_id: str, filep: str) -> None:
    """Downloads a project file from the galaxy history into the interactive tool storage.

    Args:
        dataset_id (str): the galaxy api id of the file to download
        filep (str): the directory where the interactive tool saves the file.
    """
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection()
    gi.datasets.download_dataset(
        dataset_id=dataset_id, file_path=filep, use_default_filename=False
    )


def run_refinement(dataset_id: str, delta_id: str) -> None:
    """runs the GSASII refinement: interactive executor tool in galaxy,
    using a project file and a project delta as inputs to the executor tool

    Args:
        dataset_id (str): The galaxy api id of the gsas project to run the refinement on
        delta_id (str): the galaxy api id of the delta to apply to the gsas project, before running the refinement.
        the delta contains all parameter changes made in the interactive tool.
    """
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection()
    gi.datasets.wait_for_dataset(delta_id)
    input_data = {}
    input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
    input_data["delta"] = {"values": [{"src": "hda", "id": delta_id}]}
    gi.tools.run_tool(history_id, "gpx_gsas2", input_data)


def wait_for_dataset(dataset_id: str) -> None:
    """makes the app wait until a dataset in galaxy is ready to be loaded or acted upon.

    Args:
        dataset_id (str): The galaxy api id of the dataset to wait for.
    """

    gi = get_galaxy_connection()
    gi.datasets.wait_for_dataset(dataset_id)
