import os
import shutil

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

plt.style.use('ggplot')
from hypothesis_testing import constants as cnst
from hypothesis_testing import scripts as scripts


class HypothesisTest:
    def __init__(self, data, alpha, target_column, value_column, correct_alpha=True, target_value=None,
                 test_type='two-sided'):
        """
        The Hypothesis Testing Class automates the
        :param data: Pandas dataframe containing the data
        :param alpha: The alpha used to reject the null hypothesis
        :param correct_alpha: Boolean to correct the alpha
        :param value_column: The column to test on
        :param target_column: The column to split on
        :param target_value: Individual value of target_column to hypothesis test against
        """
        self.alpha = alpha
        self.correct_alpha = correct_alpha
        self.target_column = target_column
        self.value_column = value_column
        self.target_value = target_value
        self.test_results_dir = cnst.hypothesis_tests_dir + self.target_column + "/"
        self.test_results_image_dir = self.test_results_dir + "/images/"
        self.test_type = test_type
        self.data = data.dropna(axis=0, subset=[self.target_column, self.value_column])

    def prepare_disk(self):
        """
        Prepares the disk to store the results of the hypothesis test.
        """
        print(cnst)
        if not os.path.isdir(cnst.hypothesis_tests_dir):
            os.mkdir(cnst.hypothesis_tests_dir)
        if not os.path.isdir(self.test_results_dir):
            os.mkdir(self.test_results_dir)
        contents = os.scandir(self.test_results_dir)
        [remove(item) for item in contents]

        if not os.path.isdir(self.test_results_image_dir):
            os.mkdir(self.test_results_image_dir)

    def hypothesis_test(self):
        """
        Performs the hypothesis tests using the data, target_column, value_column, and target_value
        Returns:
        """
        if self.target_value is None:
            test_indexes = list(set(self.data[self.target_column].values))
        else:
            test_indexes = self.target_value if type(self.target_value) is list else [self.target_value]

        alpha = self.alpha / (len(test_indexes) - 1) if self.correct_alpha else 0.05

        for null in test_indexes:
            results = []
            ind_results = []
            mw_results = []
            for alternative in test_indexes:
                if null == alternative:
                    continue
                a = self.data[self.data[self.target_column] == null]
                a = a[self.value_column]
                b = self.data[self.data[self.target_column] == alternative]
                b = b[self.value_column]
                if (len(b) < 30) | (len(a) < 30):
                    continue
                if (np.var(a) * np.var(b)) == 0:
                    continue
                result, mw_res, ind_res = self.process_results(null, alternative, a, b, alpha)
                results.append(result)
                mw_results.append(mw_res)
                ind_results.append(ind_res)
            if len(results) == 0:
                continue
            image = create_plot(data=self.data, column=self.target_column, value=self.value_column, target=null,
                                image_dir=self.test_results_image_dir, alpha=alpha)
            write_test_results(null, alpha, results, mw_results, ind_results, testing_dir=self.test_results_dir,
                               image=image)

    def process_results(self, null, alternative, a, b, alpha):
        ind_t, ind_p, ind_res, mw_u, mw_p, mw_res = hypothesis_test_single(a, b, alpha, alternative=self.test_type)
        result = {
            "null_rate": f'{null} has a success rate of {sum(a) / len(a)}',
            "alt_rate": f'{alternative} has a success rate of {sum(b) / len(b)}',
            "null": null,
            "alternative": alternative,
            "null_hypothesis": f'There is not a difference between {null} and {alternative}',
            "alternative_hypothesis": f'There is a difference between {null} and {alternative}',
            "alpha": f'An $/alpha$ of {alpha} was used in this test.',
            "independent_test": f'__independent t-testing__: With a t-statistic of {ind_t} and a p-value of {ind_p}, '
                                f'_{get_stats_speak(ind_res)} the null hypothssis_',
            "manwhitney_test": f'__Man-Whitney testing__: With a u-statistic of {mw_u} and a p-value of {mw_p}, '
                               f'_{get_stats_speak(mw_res)} the null hypothssis_',
            "image": create_plot(data=self.data, column=self.target_column, value=self.value_column,
                                 target=null, image_dir=self.test_results_image_dir,
                                 target_alternative=alternative, alpha=alpha)
        }
        return result, mw_res, ind_res


def write_test_results(null, alpha, results, mw_results, ind_results, testing_dir, image=None):
    with open(f"{testing_dir}{null}_test_results.md", 'w') as file_out:
        file_out.write(f'# Testing Results For {null} \n')
        file_out.write(f'$H_{{0}}$: There is not a difference in collection success against {null} \n')
        file_out.write(f'$H_{{A}}$: There is a difference in collection success against {null}\n')
        file_out.write(f'An $\\alpha$ of {alpha} was used')
        if image is not None:
            file_out.write(f'![]({"images/" + image.split("/")[-1]}) \n')
        file_out.write(
            f'Out of {len(results)} tests, there were {sum(ind_results)} rejections from {len(ind_results)} independent-t test.\n')
        file_out.write(
            f'Out of {len(results)} tests, there were {sum(mw_results)} rejections from {len(mw_results)} Man Whitney u-tests.\n')
        for result in results:
            file_out.write(f'## Testing Results for {result["null"]} against {result["alternative"]} \n')
            file_out.write(f'{result["null_rate"]}\n')
            file_out.write(f'{result["alt_rate"]}\n')
            file_out.write(f'$H_{{0}}$: {result["null_hypothesis"]}\n')
            file_out.write(f'$H_{{A}}$: {result["alternative_hypothesis"]}\n')
            file_out.write(f'{result["alpha"]}\n')
            file_out.write(f'{result["independent_test"]}\n')
            file_out.write(f'{result["manwhitney_test"]}\n')
            file_out.write(f'![]({"images/" + result["image"].split("/")[-1]}) \n')


def hypothesis_test_single(observations1, observations2, alpha, alternative='two-sided'):
    var1 = np.var(observations1)
    var2 = np.var(observations2)

    equal_var = True if (((var1 / var2) <= 4) & ((var2 / var2) <= 4)) else False

    ind_t, ind_p = stats.ttest_ind(observations1, observations2, equal_var=equal_var, alternative=alternative)

    try:
        mw_u, mw_p = stats.mannwhitneyu(observations1, observations2, alternative=alternative)
    except:
        mw_u = "Inconclusive"
        mw_p = 1

    return ind_t, ind_p, ind_p < alpha, mw_u, mw_p, mw_p < alpha


def get_stats_speak(res):
    if res:
        return 'we **reject**'
    else:
        return 'we failed to reject'


def create_plot(data, column, value, target, image_dir="", target_alternative=None,
                alpha=0.05, tail='two-sided'):
    data_test = data[data[column] == target]
    data_test = data_test[value]
    if target_alternative is None:
        data_other = data[data[column] != target]
        data_other = data_other[value]
        file_name = f'{target}_against_all_{column}.png'
        label2 = f'Non {target_alternative}'
    else:
        data_other = data[data[column] == target_alternative]
        data_other = data_other[value]
        file_name = f'{target}_against_{target_alternative}.png'
        label2 = target_alternative

    file_name = image_dir + file_name

    dist_test = get_t_dist(data_test)
    dist_other = get_t_dist(data_other)

    fig, ax = plt.subplots(figsize=(10, 5))
    x1 = np.linspace(dist_test.ppf(0.0001), dist_test.ppf(0.9999), 2000)
    x2 = np.linspace(dist_other.ppf(0.0001), dist_other.ppf(0.9999), 2000)
    ax.plot(x1, dist_test.pdf(x1), label=target);

    [ax.axvline(x, color='black', linestyle='--') for x in get_crit(dist_test, alpha, tail)]

    ax.plot(x2, dist_other.pdf(x2), label=label2);
    ax.legend(loc='best')
    ax.set_title(f"Distribution of {target} against sample")
    fig.savefig(file_name, format='png')
    plt.close(fig)
    return file_name


def get_crit(dist, alpha=0.05, tail='two-sided'):
    if tail == 'two-sided':
        lower = alpha / 2
        upper = 1 - alpha / 2
        return [dist.ppf(lower), dist.ppf(upper)]
    elif tail == 'greater':
        upper = 1 - alpha
        return [dist.ppf(upper)]
    elif tail == 'less':
        return [dist.ppf(alpha)]


def get_t_dist(data):
    mean = np.mean(data)
    se = np.std(data) / len(data) ** 0.5
    return stats.t(df=len(data) - 1, loc=mean, scale=se)


def remove(object):
    if os.path.isdir(object):
        shutil.rmtree(object)
    else:
        os.remove(object)


if __name__ == "__main__":
    ##Hypothesis Satellite Ownership
    data = scripts.aggregate_data()
    data = scripts.prepare_satnogs_data(data)
    variables = ['countries', 'SignalType', 'SignalRate', 'Frequency', 'Band']
    for variable in variables:
        hypo_tester = HypothesisTest(data=data, alpha=0.05, target_column=variable,
                                     value_column="status_numeric")
        hypo_tester.prepare_disk()
        hypo_tester.hypothesis_test()
        print(f'finished {variable}')
