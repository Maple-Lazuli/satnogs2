import json
import pandas as pd
from satellites import Satellites
from enrich_satellite_data import enrich_with_celestrak
from telemetry import Telemetry
from observation_scrapper import ObservationScrapper


def fix_freqs(freq):
    """
    Helper function to clean up the frequencies from the web scraping
    :param freq: The frequency to clean
    :return: Cleaned frequency string
    """
    if freq is None:
        return 0
    freq = freq.replace(",", "")
    return freq[:-2]


def complete_dataset(complete_path="data/"):
    """
    Creates the completed dataset by combining the events, observations, and satellite data into one dataframe.
    :param complete_path: The path to store the completed dataframe in.
    :return: Returns a copy of the completed dataframe.
    """
    with open(complete_path + "observations.json", 'r') as file_in:
        observations_df = pd.DataFrame.from_dict(json.load(file_in))
    observations_df['Frequency'] = observations_df['Frequency'].apply(lambda x: fix_freqs(x)).astype(int)
    observations_df['Observation_id'] = observations_df['Observation_id'].fillna(-1).astype(int)

    with open(complete_path + "events.json", 'r') as file_in:
        events_df = pd.DataFrame.from_dict(json.load(file_in))
    events_df['observation_id'] = events_df['observation_id'].fillna(-1).astype(int)
    events_df['norad_cat_id'] = events_df['norad_cat_id'].fillna(-1).astype(int)
    observations_df = observations_df.merge(events_df, left_on='Observation_id', right_on='observation_id', how='left')

    sat_df = pd.read_csv(complete_path + "satellites_enriched.csv")
    sat_df['norad_cat_id'] = sat_df['norad_cat_id'].fillna(-1).astype(int)
    observations_df = observations_df.merge(sat_df, on='norad_cat_id', how='left')
    observations_df.to_csv(complete_path + "complete.csv")
    return observations_df


if __name__ == '__main__':
    sat = Satellites()
    sat.get_dataframe(load_disk_first=False)
    sats_df = enrich_with_celestrak()
    sats_df.to_csv("../data/satellites_enriched.csv")
    tm = Telemetry(prints=True, max_pages=10)
    scrapper = ObservationScrapper()
    satellites = sats_df.index
    tm.clear_archived_events()
    tm.multiprocess_fetch(satellites, update_tm_events=True)
    tm_df = tm.get_events_df(save_csv=True)
    tm_df['observation_id'] = tm_df['observation_id'].fillna(0)
    tm_df['observation_id'] = tm_df['observation_id'].astype(int)
    observations = pd.unique(tm_df[tm_df['observation_id'] > 0]['observation_id'])
    scrapper.multiprocess_scrape_observations(observations)
    obs_df = scrapper.get_dataframe(save_csv=True)
    complete_dataset()

