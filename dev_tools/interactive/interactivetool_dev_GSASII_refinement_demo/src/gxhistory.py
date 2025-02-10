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
        self.history_id = history_id
        self.galaxy_url = galaxy_url
        self.api_key = api_key
        self.galaxy_instance = GalaxyInstance(url=galaxy_url, key=api_key)
        self.history = None
        self.table = None
        self.latest_entry_id = None
        self.gpx_choices = None
        self.current_gpx_id = None
        self.update()


    def update(self):

        # get the latest history data from galaxy
        self.history = self.galaxy_instance.histories.show_history(
            history_id=self.history_id,
            contents=True,
            deleted=False,
            visible=True,
            types=["dataset"],
            keys=["Id", "Hid", "Name"],
        )

        # update the new history as a pandas dataframe
        self.update_table()

        # update the selection of gpx files which can be loaded from history
        self.update_gpx_choices()


    def put(self, file_name: str, file_type: str = "auto"):
        # upload file to glaaxy history
        self.galaxy_instance.tools.upload_file(file_name, self.history_id)
        # update the local history 
        self.update()
        # wait for the dataset to be ready to use in galaxy
        self.galaxy_instance.datasets.wait_for_dataset(self.latest_entry_id)


    def get_project(self, dataset_id: str, filep: str) -> None:
        # download dataset from galaxy
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
        # format the datasets as inputs to the execution tool
        input_data = {}
        input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}
        input_data["delta"] = {"values": [{"src": "hda", "id": delta_id}]}

        # run the refinement execution static tool in galaxy
        self.galaxy_instance.tools.run_tool(self.history_id, "gpx_gsas2", input_data)

        # wait for the refinement to complete and update the local history
        self.update()
        self.galaxy_instance.datasets.wait_for_dataset(self.latest_entry_id)
        self.update()


    def update_table(self) -> pd.DataFrame:
        """gets the galaxy history from the galaxy instance and
        creates a dataframe of the history entries with
        History ids, names and Galaxy API ids.

        Returns:
            pd.DataFrame: dataframe of active entries in the galaxy history.
        """

        # create a pandas dataframe for the datasets in the history
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
        # filter the hsitory dataframe for gpx files
        gpx_df = self.table[self.table["name"].str.endswith("gpx")]

        # create a dictionary of the gpx choices
        gpx_choice_dict = dict(
            [
                (i, str(h) + ": " + fn)
                for i, h, fn in zip(gpx_df["id"], gpx_df["hid"], gpx_df["name"])
            ]
        )

        # sort the gpx_choices dictionary by history id descending
        self.gpx_choices = dict(reversed(gpx_choice_dict.items()))


    def run_generate_outputs(self, dataset_id: str) -> None:
        """runs the GSASII refinement: output generator tool in galaxy using the selected GSASII project file. CIF and CSV files will be output into the Galaxy history.

        Args:
            dataset_id (str): galaxy API id of the current GSASII project used to generate the files.
        """

        # format the datasets as inputs to for the static output tool in galaxy
        input_data = {}
        input_data["project"] = {"values": [{"src": "hda", "id": dataset_id}]}

        # run the static output tool in galaxy
        self.galaxy_instance.tools.run_tool(self.history_id, "gpx_gsas2_output", input_data)

        # wait for the output tool to finish adn update the local history
        time.sleep(2)
        self.update()
        self.galaxy_instance.datasets.wait_for_dataset(self.latest_entry_id)
        self.update()


    def get_file_hid(self, id):

        # get the relevent record in the history table
        history_entry = self.table.loc[self.table["id"] == id]

        # return the history id of the file in galaxy
        history_id = str(history_entry["hid"].loc[history_entry.index[0]])
        return history_id
