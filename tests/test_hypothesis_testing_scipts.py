from unittest import TestCase
import pandas as pd
from hypothesis_testing import hypothesis_testing_scipts as hts
from hypothesis_testing import constants as cnst


class Test(TestCase):
    def test_convert_observation_status(self):
        self.assertEqual(hts.convert_observation_status('Good'), 1, "Convert Good Observation Status")
        self.assertEqual(hts.convert_observation_status('Bad'), 0, "Convert Bad Observation Status")
        self.assertEqual(hts.convert_observation_status('Failed'), 0, "Convert Failed Observation Status")
        self.assertEqual(hts.convert_observation_status('Unknown'), 0, "Convert Unknown Observation Status")


class Test(TestCase):
    def test_aggregate_data(self):
        observations = pd.read_csv(cnst.observations_csv)
        events = pd.read_csv(cnst.events_csv)
        satellites = pd.read_csv(cnst.satellites_csv)
        combined = hts.aggregate_data()
