from django.test import TestCase
from . import dummy_orca_stuff
import orca

from orcaserver.models import Step
from orcaserver.threading import OrcaThreadSingleton


class TestThreading(TestCase):
    """Test the Injectables view"""
    def test_singleton(self):
        """"""
        thread1 = OrcaThreadSingleton()
        thread2 = OrcaThreadSingleton()
        assert thread1 == thread2