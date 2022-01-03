import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

from hypothesis_testing import constants as cnst


def aggregate_data():
    """
    returns joined dataset on satellite and observation data
    """
    satellites_df = pd.read_csv("../data/satellites_enriched.csv")
    observations_df = pd.read_csv("../data/observations.csv")
    events_df = pd.read_csv("../data/events.csv")

    sat_events_df = pd.merge(events_df, satellites_df,
                             left_on='sat_id',
                             right_on='sat_id',
                             how='left')

    complete_df = pd.merge(observations_df,
                           sat_events_df,
                           left_on='Observation_id',
                           right_on='observation_id',
                           how='left')
    return complete_df


def prepare_satnogs_data(df):
    """
    Returns: Pandas dataframe with the Status_numeric column and 1s column.
    """
    df['Ones'] = 1
    df['status_numeric'] = df['Status'].apply(lambda x: eval_obs_status(x))

    df['SignalType'] = df['Mode'].apply(lambda x: x.split(',')[0][2:-1])
    df['SignalRate'] = df['Mode'].apply(lambda x: x.split(',')[1][2:-2])
    df['SignalRate'] = df['SignalRate'].apply(lambda x: x if len(x) > 0 else '0')
    df['Frequency'] = df['Frequency'].apply(lambda x: fix_freqs(x))
    df['Frequency'] = df['Frequency'].astype(int)
    df['Band'] = df['Frequency'].apply(lambda x: label_band(x))
    df['Band'].value_counts()

    return df


def eval_obs_status(status):
    """
    returns 1 or 0 based on the status received from the Status column
    """
    if status == 'Good':
        return 1
    else:
        return 0


def sort_test_results(results):
    results = list(results)
    swap = True
    while swap:
        swap = False
        for idx in range(0, len(results) - 1):
            a = results[idx][1]
            b = results[idx + 1][1]
            if b < a:
                list_copy = results.copy()
                list_copy[idx] = results[idx + 1]
                list_copy[idx + 1] = results[idx]
                results = list_copy
                swap = True
    return results


# def hypothesis_test_greater_counts(df, indexes, column, alpha=0.05):
#     """
#     Conduct hypothesis testing against all other countries
#     """
#     bonferroni_correction = alpha / (len(indexes) - 1)
#     ind_rejects = []
#     mw_rejects = []
#     for null in indexes:
#         ind_results = []
#         mw_results = []
#         for alternative in indexes:
#             if null == alternative:
#                 continue
#             a = df[df[column] == null]
#             a = a['Status_numeric']
#             b = df[df[column] == alternative]
#             b = b['Status_numeric']
#             ind_t, ind_p, ind_res, mw_u, mw_p, mw_res = hypothesis_test(a, b, bonferroni_correction,
#                                                                         alternative='greater')
#             mw_results.append(mw_res)
#             ind_results.append(ind_res)
#         ind_rejects.append((null, sum(ind_results)))
#         mw_rejects.append((null, sum(mw_results)))
#
#     ind_rejects_sorted = sort_test_results(ind_rejects)
#     mw_rejects_sorted = sort_test_results(mw_rejects)
#     with open(f"{column}_ind_sort.txt", 'w') as file_out:
#         for result in ind_rejects_sorted:
#             file_out.write(f'{result[0]}:{result[1]}\n')
#
#     with open(f"{column}_mw_sort.txt", 'w') as file_out:
#         for result in mw_rejects_sorted:
#             file_out.write(f'{result[0]}:{result[1]}\n')


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


def label_band(freq):
    if freq <= 300 * 10 ** 6:
        return 'VHF'
    elif freq >= 2 * 10 ** 9:
        return 'GHZ'
    else:
        return 'UHF'
