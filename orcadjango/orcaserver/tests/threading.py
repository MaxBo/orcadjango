import unittest
from time import sleep
import pandas as pd
import logging
import sys

from orcaserver.management import OrcaManager


class MockStep:
    def __init__(self, name):
        self.name = name

    def save(self):
        pass


class TestOrcaInstancing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = OrcaManager()
        cls.manager.set_module('orcaserver.tests.dummy_orca_stuff')
        cls.orca1 = cls.manager.get(1)
        cls.orca2 = cls.manager.get(2)
        assert(id(cls.orca1) != id(cls.orca2))
        assert(id(cls.orca1.logger) != id(cls.orca2.logger))

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s orca1 %(message)s'))
        handler.setLevel(logging.INFO)
        cls.orca1.logger.addHandler(handler)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s orca2 %(message)s'))
        handler.setLevel(logging.INFO)
        cls.orca2.logger.addHandler(handler)

    def test_sub(self):
        step = MockStep('step1')
        self.orca1.add_injectable('dataframe', pd.DataFrame())
        self.orca2.add_injectable('dataframe', pd.DataFrame())
        self.orca1.add_injectable('inj_list', [])
        self.orca2.add_injectable('inj_list', [])
        self.manager.start(1, [step])
        self.manager.start(2, [step])

    def test_multiply(self):
        step = MockStep('step_multiply_df')
        mult1 = 5
        df1 = pd.DataFrame(['A', 'B', 'C'])
        mult2 = 3
        df2 = pd.DataFrame([1, 2, 3])

        # add_injectable acts like a setter and overwrites, weird
        self.orca1.add_injectable('inj_int', mult1)
        # the steps will change the dataframe in place
        self.orca1.add_injectable('dataframe', df1.copy())
        self.manager.start(1, [step, step])

        # wait a little before setting uo and starting the second orca instance
        # to see if there are side effects and if it messes up the running one
        sleep(1.5)

        self.orca2.add_injectable('inj_int', mult2)
        self.orca2.add_injectable('dataframe', df2.copy())
        self.manager.start(2, [step, step])

        # there might be a better way for waiting for the thread
        while self.manager.is_running(1) or self.manager.is_running(2):
            sleep(0.5)

        assert((self.orca1.get_injectable('dataframe').values ==
               (df1 * mult1 * mult1).values).all())
        assert((self.orca2.get_injectable('dataframe').values ==
               (df2 * mult2 * mult2).values).all())
        assert(self.orca1.get_injectable('inj_int') == mult1)
        assert(self.orca2.get_injectable('inj_int') == mult2)

