from django.views.generic import ListView, FormView
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.conf import settings
import logging
import json
from django.utils import timezone
import logging

from orcadjango.loggers import OrcaChannelHandler
from orcaserver.models import LogEntry
from orcaserver.forms import ProjectForm
from orcaserver.models import Scenario, Project, Injectable
from orcaserver.management import (OrcaManager, OrcaTypeMap)

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
            handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
            manager.add_log_handler(scenario.id, handler)
            apply_injectables(orca, scenario)
        return orca

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        project = self.get_project()
        scenario = self.get_scenario()
        module = self.get_module()
        kwargs['active_project'] = project
        kwargs['active_scenario'] = scenario
        kwargs['python_module'] = module
        kwargs['show_project_settings'] = True
        return kwargs


class ProjectsView(ProjectMixin, ListView):
    model = Project
    template_name = 'orcaserver/projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """Return the injectables with their values."""
        projects = self.model.objects.filter(module=self.get_module())
        return projects

    def post(self, request, *args, **kwargs):
        project_id = request.POST.get('project')
        if project_id:
            if request.POST.get('select'):
                self.request.session['project'] = int(project_id)
                self.request.session['scenario'] = None
                return HttpResponseRedirect(reverse('scenarios'))
            elif request.POST.get('delete'):
                Project.objects.get(id=project_id).delete()
        return HttpResponseRedirect(request.path_info)


class ProjectView(ProjectMixin, FormView):
    form_class = ProjectForm
    template_name = 'orcaserver/project.html'
    success_url = '/projects'

    def get_context_data(self, **kwargs):
        project_id = self.kwargs.get('id')
        kwargs = super().get_context_data(**kwargs)
        kwargs['title'] = 'Change Project' if project_id else 'Add Project'
        return kwargs

    def get_template_names(self):
        project_id = self.kwargs.get('id')
        try:
            project = Project.objects.get(id=project_id)
            module = project.module
        except ObjectDoesNotExist:
            module = self.get_module()
        available = settings.ORCA_MODULES.get('available', {})
        rev = {p['path']: p.get('template') for p in available.values()}
        template = rev.get(module)
        if not template:
            template = settings.ORCA_MODULES.get('default', {}).get(
                'template', self.template_name)
        return [template]

    def get_form_kwargs(self):
        project_id = self.kwargs.get('id')
        kwargs = super().get_form_kwargs()
        kwargs['module'] = self.get_module()
        # ToDo: catch errors if project does not exist (maybe already
        # in get() or post())
        if project_id is not None:
            project = Project.objects.get(id=project_id)
            kwargs['project_name'] = project.name
            kwargs['project_description'] = project.description
            kwargs['init'] = project.init
        return kwargs

    def form_valid(self, form):
        project_id = self.kwargs.get('id')
        fields = form.cleaned_data.copy()
        name = fields.pop('name')
        description = fields.pop('description')
        init = {}
        # additional fields are assumed to be injectable values
        for field, value in fields.items():
            conv = OrcaTypeMap.get(type(value))
            init[field] = conv.to_str(value)
        if project_id is None:
            Project.objects.create(name=name, description=description,
                                   init=json.dumps(init),
                                   module=self.get_module())
        else:
            project = Project.objects.get(id=project_id)
            project.name = name
            project.description = description
            project.init = json.dumps(init)
            project.save()
        return super().form_valid(form)

class ExtractProjectView(ProjectMixin, FormView):
    ''''''

