import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

import constants as cnst


class Hypothesis_Test:
    def __init__(self, data, alpha, correct_alpha=True):
        """
        The Hypothesis Testing Class automates the
        :param data: Pandas dataframe containing the data
        :param alpha: The alpha used to reject the null hypothesis
        :param correct_alpha: Boolean to correct the alpha
        """
        self.data = data
        self.alpha_base = alpha
        self.correct_alpha = correct_alpha


