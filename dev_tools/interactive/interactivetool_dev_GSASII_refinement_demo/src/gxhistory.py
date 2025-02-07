from bioblend.galaxy import GalaxyInstance
import logging
import os
import typing
import pandas as pd
import time

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
logging.getLogger("bioblend").setLevel(logging.CRITICAL)
log = logging.getLogger()

class HistoryModel:
    def __init__(self, history_id, galaxy_url, api_key):
        self.name = history_id
        self.galaxy_url = galaxy_url
        self.api_key = api_key
        self.galaxy_instance = GalaxyInstance(url=galaxy_url, key=api_key)
        self.history = None
        self.table = None
        self.latest_entry_id = None
        self.gpx_choices = None
        self.update()


    def update(self):
        self.history = self.galaxy_instance.histories.show_history(
            history_id=self.history_id,
            contents=True,
            deleted=False,
            visible=True,
            types=["dataset"],
            keys=["Id", "Hid", "Name"],
        )
        self.update_table()
        self.update_gpx_choices()


    def put(self, file_name: str, file_type: str = "auto"):
        self.galaxy_instance.tools.upload_file(file_name, self.history_id)


    def get_project(self, dataset_id: str, filep: str) -> None:
        self.galaxy_instance.datasets.download_dataset(
            dataset_id=dataset_id, file_path=filep, use_default_filename=False
        )


    def run_refinement(self, dataset_id: str, delta_id: str) -> None:
        """runs the GSASII refinement: interactive executor tool in galaxy,
        using a project file and a project delta as inputs to the executor tool

        Args:
            dataset_id (str): The galaxy api id of the gsas project to run the refinement on
            delta_id (str): the galaxy api id of the delta to apply to the gsas project, before running the refinement.
            the delta contains all parameter changes made in the interactive tool.
        """

        self.galaxy_instance.datasets.wait_for_dataset(delta_id)
        input_data = {}
        input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
        input_data["delta"] = {"values": [{"src": "hda", "id": delta_id}]}
        self.galaxy_instance.tools.run_tool(self.history_id, "gpx_gsas2", input_data)

    def update_table(self) -> pd.DataFrame:
        """gets the galaxy history from the galaxy instance and
        creates a dataframe of the history entries with
        History ids, names and Galaxy API ids.

        Returns:
            pd.DataFrame: dataframe of active entries in the galaxy history.
        """
        history_df: pd.DataFrame = pd.DataFrame(self.history)
        self.table = history_df[["hid", "name", "id"]]

        # set the latest entry id
        row_id: int = self.table["hid"].idxmax()
        self.latest_entry_id: str = self.table.loc[row_id, "id"]


    def update_gpx_choices(self) -> dict:
        """creates a dictionary of GSASII projects in the galaxy history
        which can be loaded into the interactive tool.

        Returns:
            dict: dictionary of GSASII project files in the galaxy history
            with keys of their Galaxy API IDs and values of
            "history IDs: filename"
        """
        gpx_df = self.history_table[self.history_table["name"].str.endswith("gpx")]
        gpx_choice_dict = dict(
            [
                (i, str(h) + ": " + fn)
                for i, h, fn in zip(gpx_df["id"], gpx_df["hid"], gpx_df["name"])
            ]
        )

        self.gpx_choices = dict(reversed(gpx_choice_dict.items()))

    def run_generate_outputs(self, dataset_id: str) -> None:
        """runs the GSASII refinement: output generator tool in galaxy using the selected GSASII project file. CIF and CSV files will be output into the Galaxy history.

        Args:
            dataset_id (str): galaxy API id of the current GSASII project used to generate the files.
        """

        input_data = {}
        input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
        self.galaxy_instance.tools.run_tool(self.history_id, "gpx_gsas2_output", input_data)
        time.sleep(2)
        self.update()
        self.galaxy_instance.datasets.wait_for_dataset(self.latest_entry_id)


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


def run_generate_outputs(dataset_id: str) -> None:
    """runs the GSASII refinement: output generator tool in galaxy using the selected GSASII project file. CIF and CSV files will be output into the Galaxy history.

    Args:
        dataset_id (str): galaxy API id of the current GSASII project used to generate the files.
    """
    history_id = os.environ["HISTORY_ID"]
    gi = get_galaxy_connection()
    input_data = {}
    input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
    gi.tools.run_tool(history_id, "gpx_gsas2_output", input_data)
    id = refresh_latest_history_entry_id()
    wait_for_dataset(id)


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


def get_update_history() -> pd.DataFrame:
    """gets the galaxy history from the galaxy instance and
    creates a dataframe of the history entries with
    History ids, names and Galaxy API ids.

    Returns:
        pd.DataFrame: dataframe of active entries in the galaxy history.
    """
    history = gx_update_history()
    history_df: pd.DataFrame = pd.DataFrame(history)
    history_table = history_df[["hid", "name", "id"]]

    return history_table


def refresh_latest_history_entry_id() -> str:
    """Finds the API id of the latest files in the galaxy history.

    Returns:
        str: Galaxy API ID for the most recent entry in the history.
    """
    time.sleep(2)
    hist_table = get_update_history()
    row_id: int = hist_table["hid"].idxmax()
    id: str = hist_table.loc[row_id, "id"]
    return id


def get_gpx_choices() -> dict:
    """creates a dictionary of GSASII projects in the galaxy history
    which can be loaded into the interactive tool.

    Returns:
        dict: dictionary of GSASII project files in the galaxy history
        with keys of their Galaxy API IDs and values of
        "history IDs: filename"
    """
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
