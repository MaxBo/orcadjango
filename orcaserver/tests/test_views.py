from django.test import TestCase
from . import dummy_orca_stuff
import orca

class TestInjectables(TestCase):
    """Test the Injectables view"""
    def test_1(self):
        """"""
        orca.run(['step1', 'step2', 'step_dict'])
