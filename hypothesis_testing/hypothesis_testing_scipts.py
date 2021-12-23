import pandas as pd
import constants as cnst


def aggregate_data():
    """
    Returns:
        Pandas Dataframe that contains a merged dataset of satellites_csv, observations_csv, and
        events_csv
    """
    satellites_df = pd.read_csv(cnst.satellites_csv)
    observations_df = pd.read_csv(cnst.observations_csv)
    events_df = pd.read_csv(cnst.events_df)

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


def convert_observation_status(status):
    """
    Converts the observation status into a usable format
    Args:
        status: Status string (i.e. 'Good', 'Bad', 'Unkown', etc)

    Returns:
        Integer 1 or 0 to indicate if the observation was successful
    """
    if status == 'Good':
        return 1
    else:
        return 0

def get_stats_speak(res):
    """
    Interprets the result of hypothesis testing
    Args:
        res: Boolean indicating the p-value was less than or greater than
        the alpha threshold

    Returns:
        String stating the results of the test
    """
    if res:
        return 'we **reject**'
    else:
        return 'we failed to reject'