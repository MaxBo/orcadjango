import logging
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from orcadjango.loggers import OrcaChannelHandler
from orcaserver.models import LogEntry
from orcaserver.models import Scenario, Project
from orcaserver.injectables import Injectable
from orcaserver.management import OrcaManager

manager = OrcaManager()

def apply_injectables(orca, scenario):
    if not scenario:
        return
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        if inj.can_be_changed:
            orca.add_injectable(inj.name, inj.validated_value)


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


class ProjectMixin:

    def get_project(self):
        """get the selected scenario"""
        project_pk = self.request.session.get('project')
        module = self.get_module()
        try:
            project = Project.objects.get(pk=project_pk, module=module)
        except ObjectDoesNotExist:
            project = None
            self.request.session['project'] = None
            self.request.session['scenario'] = None
        return project

    def get_module(self):
        module = self.request.session.get('module')
        if not module:
            module = self.request.session['module'] = \
                OrcaManager().default_module
        return module

    def get_scenario(self):
        """get the selected scenario"""
        scenario_pk = self.request.session.get('scenario')
        try:
            scenario = Scenario.objects.get(pk=scenario_pk)
        except ObjectDoesNotExist:
            project_pk = self.request.session.get('project')
            scenarios = Scenario.objects.filter(project_id=project_pk)
            if scenarios:
                scenario = scenarios.first()
                self.request.session['scenario'] = scenario.pk
            else:
                scenario = None
        return scenario

    def get_orca(self, scenario=None):
        scenario = scenario or self.get_scenario()
        if not scenario:
            return
        module = self.get_module()
        orca = manager.get(scenario.id, module=module, create=False)
        if not orca:
            orca = manager.create(scenario.id, module=module)
            handler = ScenarioHandler(scenario, persist=True)
            level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
            handler.setLevel(level)
            manager.add_log_handler(scenario.id, handler)
            apply_injectables(orca, scenario)
        return orca

    def get_context_data(self, **kwargs):
        # workaround for forms etc. requesting orca without applying values
        orca = self.get_orca()
        kwargs = super().get_context_data(**kwargs)
        project = self.get_project()
        scenario = self.get_scenario()
        module = self.get_module()
        module_meta = {}
        # get pretty name of module
        if settings.ORCA_MODULES:
            for k, v in settings.ORCA_MODULES['available'].items():
                if v.get('path') == module:
                    module = k
                    module_meta = v
        kwargs['active_project'] = project
        kwargs['active_scenario'] = scenario
        kwargs['python_module'] = module
        kwargs['data_text'] = module_meta.get('data_text')
        data_url = module_meta.get('data_url', {})
        kwargs['data_url_name'] = data_url.get('name', 'Data')
        kwargs['data_url_href'] = data_url.get('href', data_url.get('url'))
        kwargs['data_url'] = data_url.get('url')
        kwargs['show_project_settings'] = True
        return kwargs