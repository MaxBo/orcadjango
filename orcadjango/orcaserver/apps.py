from django.apps import AppConfig
from django.conf import settings

from orcaserver.management import OrcaManager


class OrcaserverConfig(AppConfig):
    name = 'orcaserver'

    def ready(self):
        OrcaManager().set_module(settings.ORCA_MODULES['default']['path'])
