from django.apps import AppConfig
from django.conf import settings

from orcaserver.management import OrcaManager


class OrcaserverConfig(AppConfig):
    name = 'orcaserver'

    def ready(self):
        default_module = settings.ORCA_MODULES['default']
        module_path = settings.ORCA_MODULES['available'][default_module]['path']
        OrcaManager.default_module = module_path
        # concurrent creation of empty orca shells was fixed due to missing lock
        # in threading, but to be on the safe side:
        # create the generic instances of all known modules on start
        for k, v in settings.ORCA_MODULES['available'].items():
            OrcaManager(v['path'])
