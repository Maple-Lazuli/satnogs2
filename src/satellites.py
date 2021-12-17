from os.path import exists
import json

import pandas as pd
import requests

import constants as cnst

sat_json = "../data/satellites.json"


class Satellites:
    def __init__(self, api=cnst.api, endpoint=cnst.satellites, prints=True):
        """
        The satellites class uses HTTP GET to create a JSON or DATAFRAME of satellites from SATNOGS
        :param api: The name of the host to pull data from
        :param endpoint: The endpoint to query from the host
        :param prints: Boolean for whether print statements should be executed.
        """
        self.api = api
        self.endpoint = endpoint
        self.response_json = None
        self.dataframe_path = "../data/sats.csv"
        self.prints = prints

    def get_dataframe(self, load_disk_first=True, save_csv=True):
        """
        Get a dataframe from the collected JSON by either reading from the disk if it is archived or by fetching
        the data again.
        :param load_disk_first: Boolean on whether to read from the local disk first or fetch the data.
        :param save_csv: Boolean on whether to save the dataframe as a CSV after loading to speed up future calls
        :return: Returns a pandas dataframe with the index as the satellite's NORAD
        """
        if load_disk_first:
            print("Trying to load CSV") if self.prints else None
            if exists(self.dataframe_path):
                sats_df = pd.read_csv(self.dataframe_path)
                return self.fix_df_index(sats_df)
        if self.response_json is None:
            self.get_data(load_disk_first)
        sats_df = pd.DataFrame.from_dict(self.response_json)
        print("Saved satellites CSV to disk") if self.prints else None
        sats_df.to_csv(self.dataframe_path, index=False)
        return self.fix_df_index(sats_df)

    @staticmethod
    def fix_df_index(df):
        """
        Modifies the datframe to use the norad idenfier
        :param df:The dataframe to modify
        :return:pandas dataframe with a the norad id as the index
        """
        df['norad_cat_id'] = df['norad_cat_id'].fillna(0)
        df['norad_cat_id'] = df.norad_cat_id.astype("int")
        df.set_index(['norad_cat_id'], inplace=True)
        return df

    def get_data(self, load_disk_first=True):
        """
        Gets the JSON of the satellites by either fetching the data for loading from the disk.
        :param load_disk_first: Attempt to load from the disk first.
        :return: Returns a JSON of the satellites
        """
        if load_disk_first:
            print("Trying to load JSON from disk") if self.prints else None
            if exists(sat_json):
                with open(sat_json, 'r') as file_in:
                    self.response_json = json.load(file_in)
            return self.response_json
        else:
            self.fetch_json()
            return self.response_json

    def fetch_json(self, write_json=True, write_name=sat_json):
        """
        Fetches the Satellite JSON from the api endpoint
        :param write_json: Boolean on whether to write a copy of the fetched JSON to the disk
        :param write_name: String for the name the json should be written as.
        :return: None. Updates the response_json
        """
        print(f"Fetching From {self.api + self.endpoint}") if self.prints else None
        res = requests.get(
            self.api + self.endpoint,
            headers={
                "accept": "application/json",
                "Authorization": cnst.keys['api'],
                "Cookie": cnst.keys['cookie'],
                "X-CSRFToken": cnst.keys['token']})
        print(f"HTTP GET Response Code: {res.status_code}") if self.prints else None
        self.response_json = res.json()
        if write_json:
            with open(write_name, 'w') as out:
                json.dump(self.response_json, out)


if __name__ == '__main__':
    sats = Satellites()
    print(" Fetch")
    sats.fetch_json()
    print("Fetched Data:")
    print(sats.response_json)
    print(f"Does {sat_json} exist: {exists(sat_json)}")
    print("Data Load")
    sats.get_data()
    print("DataFrame")
    print(sats.get_dataframe(load_disk_first=False).head())
