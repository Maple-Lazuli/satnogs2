import pandas as pd
import numpy as np
from scipy import stats                  
import matplotlib.pyplot as plt


def aggregate_data():
    """
    returns joined dataset on satellite and observeration data
    """
    satellites_df = pd.read_csv("../data/satellites_enriched.csv")
    observations_df = pd.read_csv("../data/observations.csv")
    events_df = pd.read_csv("../data/events.csv")
    
    sat_events_df = pd.merge(events_df, satellites_df, 
                             left_on='sat_id', 
                             right_on='sat_id', 
                             how = 'left')
    
    complete_df = pd.merge(observations_df, 
                           sat_events_df, 
                           left_on='Observation_id', 
                           right_on='observation_id', 
                           how = 'left')
    return complete_df

def eval_obs_status(status):
    """
    returns 1 or 0 based on the status recieved from the Status column
    """
    if status == 'Good':
        return 1
    else:
        return 0


def get_stats_speak(res):
    if res:
        return 'we **reject**'
    else:
        return 'we failed to reject'


def hypothesis_test(observations1, observations2, alpha, alternative = 'two-sided' ):
    var1 = np.var(observations1)
    var2 = np.var(observations2)
    
    equal_var = True if (((var1 / var2) <= 4) & ((var2 / var2) <=4) ) else False
    
    ind_t, ind_p = stats.ttest_ind(observations1, observations2, equal_var= equal_var, alternative=alternative)
    
    try:
        mw_u, mw_p = stats.mannwhitneyu(observations1, observations2, alternative = alternative)
    except:
        mw_u = "Inconclusive"
        mw_p = 1
    
    return ind_t, ind_p, ind_p < alpha, mw_u, mw_p, mw_p < alpha

def hypothesis_test_column(df, indexes, column,value, testing_dir, alpha = 0.05):
    """
    Conduct hypothesis testing against all other columns
    """
    bonferroni_correction = alpha / (len(indexes) - 1)
    for null in indexes:
        results = []
        ind_results = []
        mw_results = []
        for alternative in indexes:
            if null == alternative:
                continue
            a = df[df[column] == null]
            a = a[value]
            b = df[df[column] == alternative]
            b = b[value]
            ind_t, ind_p, ind_res, mw_u, mw_p, mw_res = hypothesis_test(a, b, bonferroni_correction)
            result = {
                "null_rate": f'{null} has a success rate of {sum(a)/len(a)}',
                "alt_rate": f'{alternative} has a success rate of {sum(b)/len(b)}',
                "null": null,
                "alternative": alternative,
                "null_hypothesis": f'There is not a difference between {null} and {alternative}',
                "alternative_hypothesis": f'There is a difference between {null} and {alternative}',
                "alpha": f'Starting with an alpha of {alpha}, it was corrected to {bonferroni_correction}',
                "independent_test": f'__independent t-testing__: With a t-statistic of {ind_t} and a p-value of {ind_p}, _{get_stats_speak(ind_res)} the null hypothssis_',
                "manwhitney_test": f'__Man-Whitney testing__: With a u-statistic of {mw_u} and a p-value of {mw_p}, _{get_stats_speak(mw_res)} the null hypothssis_',
                "image": create_exclusive_histogram(data = df, column = column, value = value, target = null,target_alternative = alternative, alpha = alpha)
            }
            results.append(result)
            mw_results.append(mw_res)
            ind_results.append(ind_res)
        write_test_results(null, alpha, bonferroni_correction, results, mw_results, ind_results, testing_dir)


def write_test_results(null, alpha, correction, results, mw_results, ind_results, testing_dir = "../hypothesis_tests/countries/"):
    with open(f"{testing_dir}{null}_test_results.md", 'w') as file_out:
        file_out.write(f'# Testing Results For {null} \n')
        file_out.write(f'$H_{{0}}$: There is not a difference in collection success against {null} \n')
        file_out.write(f'$H_{{A}}$: There is a difference in collection success against {null}\n')
        file_out.write(f'Out of {len(results)} tests, there were {sum(ind_results)} rejections from {len(ind_results)} independent-t test.\n')
        file_out.write(f'Out of {len(results)} tests, there were {sum(mw_results)} rejections from {len(mw_results)} Man Whitney u-tests.\n')
        for result in results:
            file_out.write(f'## Testing Results for {result["null"]} against {result["alternative"]} \n')
            file_out.write(f'{result["null_rate"]}\n')
            file_out.write(f'{result["alt_rate"]}\n')
            file_out.write(f'$H_{{0}}$: {result["null_hypothesis"]}\n')
            file_out.write(f'$H_{{A}}$: {result["alternative_hypothesis"]}\n')
            file_out.write(f'{result["alpha"]}\n')
            file_out.write(f'{result["independent_test"]}\n')
            file_out.write(f'{result["manwhitney_test"]}\n')

def create_exclusive_histogram(data, column, value, target,target_alternative = None, alpha = 0.05, tail='two-sided'):
    
    data_test =data[data[column] == target]
    data_test = data_test[value]
    if target_alternative is None:
        data_other = data[data[column] != target]
        data_other = data_other[value]
        file_name = f'{target}_against_all_{column}.png'
    else:
        data_other = data[data[column] == target_alternative]
        data_other = data_other[value]
        file_name = f'{target}_against_{target_alternative}.png'
    
    dist_test = get_t_dist(data_test)
    dist_other = get_t_dist(data_other)
    
    fig, ax = plt.subplots(figsize=(20, 15))
    x1 = np.linspace(dist_test.ppf(0.0001),dist_test.ppf(0.9999), 2000)
    x2 = np.linspace(dist_other.ppf(0.0001),dist_other.ppf(0.9999), 2000)
    ax.plot(x1, dist_test.pdf(x1), label=target);
    
    [ax.axvline(x, color='black', linestyle='--') for x in get_crit(dist_test, alpha, tail)]
    
    ax.plot(x2, dist_other.pdf(x2), label=f'Non {target}');
    ax.legend(loc='best')
    ax.set_title(f"Distribution of {target} against sample")
    fig.savefig(file_name, format='png')
    return file_name

def get_crit(dist, alpha=0.05, tail='two-sided'):
    if tail =='two-sided':
        lower = alpha/2
        upper = 1 - alpha/2
        return [dist.ppf(lower),dist.ppf(upper)]
    elif tail == 'greater':
        upper = 1 - alpha
        return [dist.ppf(upper)]
    elif tail == 'less':
        return [dist.ppf(alpha)]

def get_t_dist(data):
    mean = np.mean(data)
    se = np.std(data) / len(data)**0.5
    return stats.t(df = len(data)-1, loc = mean, scale = se)

def sort_test_results(results):
    results = list(results)
    swap = True
    while swap != False:
        swap = False
        for idx in range(0, len(results)-1):
            a = results[idx][1]
            b = results[idx+1][1]
            if b < a:
                list_copy = results.copy()
                list_copy[idx] = results[idx+1]
                list_copy[idx+1] = results[idx]
                results = list_copy
                swap = True
    return results


def hypothesis_test_greater_counts(df, indexes, column, alpha = 0.05):
    """
    Conduct hypothesis testing against all other countries
    """
    bonferroni_correction = alpha / (len(indexes) - 1)
    ind_rejects = []
    mw_rejects = []
    for null in indexes:
        ind_results = []
        mw_results = []
        for alternative in indexes:
            if null == alternative:
                continue
            a = df[df[column] == null]
            a = a['Status_numeric']
            b = df[df[column] == alternative]
            b = b['Status_numeric']
            ind_t, ind_p, ind_res, mw_u, mw_p, mw_res = hypothesis_test(a, b, bonferroni_correction, alternative='greater')
            mw_results.append(mw_res)
            ind_results.append(ind_res)
        ind_rejects.append((null, sum(ind_results)))
        mw_rejects.append((null, sum(mw_results)))
    
    ind_rejects_sorted = sort_test_results(ind_rejects)
    mw_rejects_sorted = sort_test_results(mw_rejects)
    with open(f"{column}_ind_sort.txt", 'w') as file_out:
        for result in ind_rejects_sorted:
            file_out.write(f'{result[0]}:{result[1]}\n')
        
    with open(f"{column}_mw_sort.txt", 'w') as file_out:
        for result in mw_rejects_sorted:
            file_out.write(f'{result[0]}:{result[1]}\n')


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