from os import listdir, remove
from os.path import exists, isfile
import json
from multiprocessing import Pool

import pandas as pd
import requests

import constants as cnst


class Telemetry:
    def __init__(self, events_path="../data/telemetry_events/", completed_path="../data/", prints=True,
                 max_pages=1000000):
        """
        Queries the telemetry endpoint for satellite observation events.
        :param events_path: The path the events should be stored in individually
        :param completed_path: The path for the compiled json of all the events
        :param prints: Boolean on whether to print to the screen
        :param max_pages: The max number of pages per satellites. There are typically 25 events per page.
        """
        self.telemetry_events = []
        self.events_path = events_path
        self.completed_path = completed_path
        self.completed_json = self.completed_path + "events.json"
        self.completed_df = self.completed_path + "events.csv"
        self.prints = prints
        self.max_pages = max_pages

    @staticmethod
    def get_url_endpoint(norad, page=None, tm_endpoint=cnst.telemetry, site=cnst.api):
        """
        Create the url to query for the satellite
        :param norad: The norad of the satellite to query
        :param page: The page number to pull
        :param tm_endpoint: The endpoint to pull from
        :param site: The site or api to reach
        :return: The query string to get the telemetry observations
        """
        rtn_str = site + tm_endpoint
        rtn_str += ("page=" + str(page) + "&") if (page is not None) else ""
        rtn_str += "satellite=" + str(norad)
        return rtn_str

    def fetch_telemetry_by_satellite(self, norad, write_events=True):
        """
        Fetch telemetry observation events for a satellite identified by its norad
        :param norad: The norad of the satellite to pull from
        :param write_events: Boolean on whether to write the observation events to the disk
        :return: list of observation json events
        """
        headers_dict = {"accept": "application/json", "Authorization": f"token {cnst.keys['api']}"}
        norad = str(norad)
        return_jsons = []
        r = requests.get(
            self.get_url_endpoint(norad),
            headers=headers_dict)
        if r.status_code != 200:
            print(f'HTTP status {r.status_code} received for {norad}') if self.prints else None
            return []

        return_jsons = return_jsons + r.json()
        page_count = 1
        print(f'found {len(r.json())} events for {norad}') if self.prints else None
        if 'link' in r.headers.keys():
            while r.headers['link'].find('rel="next"') != -1:
                if self.max_pages < page_count:
                    print(f"Page count exceeded for {norad}") if self.prints else None
                    break
                r = requests.get(
                    self.get_url_endpoint(norad, page=page_count),
                    headers=headers_dict)
                if r.status_code != 200:
                    print(f"HTTP status {r.status_code} received for {norad}") if self.prints else None
                    print(f"{len(return_jsons)} observations were collected for {norad}") if self.prints else None
                    break
                return_jsons = return_jsons + r.json()
                if page_count % 100 == 0 & self.prints:
                    print(f"page {page_count} for {norad}")
                page_count += 1

        print(f"Finished {norad} with {len(return_jsons)} events") if self.prints else None
        if write_events & (len(return_jsons) > 0):
            with open(f"{self.events_path}{norad}.json", 'w') as out:
                json.dump(return_jsons, out)
        return return_jsons

    def get_satellite_events_by_norad(self, norads, check_disk=True, empty_list=True, fetch=True, save_events=True):
        """
        Fetch observation events for a satellites identified in a list of norads
        :param norads: The list of satellite norads to pull for
        :param check_disk: Check the local disk before fetching telemetry observation events
        :param empty_list: Empty the telemetry observation events prior to fetching data
        :param fetch: Boolean on whether to fetch the data from the api
        :param save_events: Boolean on whether to save the object's telemetry observation events list to the disk
        :return: None The instantiated object's telemetry observations list is updated
        """
        if empty_list:
            self.telemetry_events = []
        for norad in norads:
            if check_disk & exists(f"{self.events_path}{norad}.json"):
                print(f'reading norad {norad} from disk') if self.prints else None
                with open(f"{self.events_path}{norad}.json", 'r') as file_in:
                    self.telemetry_events = self.telemetry_events + json.load(file_in)
            elif fetch:
                print(f'fetching norad {norad} from {cnst.api}') if self.prints else None
                fetch = self.fetch_telemetry_by_satellite(norad)
                if len(fetch) > 0:
                    self.telemetry_events = self.telemetry_events + fetch

        if save_events:
            with open(f'{self.completed_json}', 'w') as out:
                json.dump(self.telemetry_events, out)

    def multiprocess_fetch(self, norads, update_tm_events=False):
        """
        Functions very similar to get_satellite_events_by_norad except it uses multiple processes.
        Each process will create an archive on this disk that can all be read into memory with
         get_archived_satellites_events
        :param norads: The list of norads to pull for
        :param update_tm_events: boolean on whether to update the instantiated object's telemetry events list
        :return: None
        """
        pool = Pool()
        pool.map(self.fetch_telemetry_by_satellite, norads)
        if update_tm_events:
            self.get_satellite_events_by_norad(norads, fetch=False)

    def get_archived_satellites_events(self, empty_list=True, save_events=True):
        """
        Read in the archived telemetry events
        :param empty_list: Boolean on whether to empty the telemetry events list
        :param save_events: Boolean on whether to save the telmetry events list to the disk
        :return: None
        """
        if empty_list:
            self.telemetry_events = []
        for file in listdir(self.events_path):
            file_name = f'{self.events_path}{file}'
            if isfile(file_name):
                with open(file_name, 'r') as file_in:
                    self.telemetry_events = self.telemetry_events + json.load(file_in)
        if save_events:
            with open(f'{self.completed_json}', 'w') as out:
                json.dump(self.telemetry_events, out)
                print(f"Updated {self.completed_json}") if self.prints else None

    def clear_archived_events(self):
        """
        Clears the archived telemetry observations
        :return: None
        """
        for file in listdir(self.events_path):
            file_name = f'{self.events_path}{file}'
            if isfile(file_name):
                remove(file_name)
                print(f"Removed {file_name}") if self.prints else None
        if exists(self.completed_json):
            remove(self.completed_json)
            print(f"Removed {self.completed_json}") if self.prints else None
        if exists(self.completed_df):
            remove(self.completed_df)
            print(f"Removed {self.completed_df}") if self.prints else None

    def get_events_df(self, load_from_disk=True, save_csv=True):
        """
        Get a dataframe from the observations events.
        :param load_from_disk: Boolean on whether to load from disk or use the list in memory
        :param save_csv:
        :return: pandas dataframe
        """
        if load_from_disk:
            print("Trying To Load Telemetry ") if self.prints else None
            if exists(self.completed_df):
                print("Loading Telemetry Events From CSV") if self.prints else None
                return pd.read_csv(self.completed_df)
            elif exists(self.completed_json):
                with open(self.completed_json, 'r') as file_in:
                    df = pd.DataFrame.from_dict(json.load(file_in))
                    print("Loading Telemetry Events From Json File") if self.prints else None
        elif len(self.telemetry_events) > 0:
            df = pd.DataFrame.from_dict(self.telemetry_events)
            print("Loading Telemetry Events From Memory") if self.prints else None
        else:
            print("Event Data Needs to be fetched")
            return None
        if save_csv:
            print("Saving Dataframe as CSV") if self.prints else None
            df.to_csv(self.completed_df, index=False)
        return df


if __name__ == '__main__':
    tm = Telemetry()
    print("Get URL")
    print(tm.get_url_endpoint("25544"))
    print("Telemetry Fetch")
    print(tm.fetch_telemetry_by_satellite(26609)[3])
    print("Fetching for Several Satellites")
    tm.get_satellite_events_by_norad([14781, 22825, 25338])
    print(tm.telemetry_events[4])
    print("Clearing Archive")
    tm.clear_archived_events()
    print("Multiprocess Fetch")
    tm.multiprocess_fetch([26063, 26609, 22825, 25338, 20442, 27844])
    print("Loading From Archive")
    tm.get_archived_satellites_events()
    print(tm.telemetry_events[4])
    print("Getting Observation Events DF")
    print(tm.get_events_df().head())
    print(tm.get_events_df().columns)
