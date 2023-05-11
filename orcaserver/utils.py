import logging
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from orcadjango.loggers import OrcaChannelHandler
from orcaserver.models import LogEntry
from orcaserver.models import Scenario, Project
from orcaserver.management import OrcaManager


class ScenarioHandler(OrcaChannelHandler):
    def __init__(self, scenario, persist=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = f'log_{scenario.id}'
        self.scenario = scenario
        self.setFormatter(logging.Formatter(
            f'%(asctime)s,%(msecs)03d {scenario.name} - %(message)s',
            '%d.%m.%Y %H:%M:%S'))
        self.persist = persist

    def emit(self, record):
        try:
            if not self.persist:
                return
            LogEntry.objects.create(
                scenario=self.scenario,
                message=record.getMessage(),
                timestamp=timezone.now(),
                level=record.levelname
            )
            super().emit(record)
        except OSError as e:
            print('Error while connecting to Redis')
