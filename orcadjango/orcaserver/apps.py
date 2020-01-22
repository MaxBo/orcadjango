from django.apps import AppConfig
from django.conf import settings
from orcaserver.management.commands import runorca


class OrcaserverConfig(AppConfig):
    name = 'orcaserver'

    def ready(self):
        runorca.load_module(settings.ORCA_MODULE)
