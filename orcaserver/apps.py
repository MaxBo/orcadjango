from django.apps import AppConfig

from orcaserver.orca import OrcaManager


class OrcaserverConfig(AppConfig):
    name = 'orcaserver'

    def ready(self):
        # concurrent creation of empty orca shells was fixed due to missing lock
        # in threading, but to be on the safe side:
        # create the generic instances of all known modules on start
        from .models import Module
        try:
            for module in Module.objects.all():
                OrcaManager(module.path)
        except:
            pass
