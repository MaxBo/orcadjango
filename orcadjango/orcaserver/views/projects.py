from django.views.generic import ListView, FormView
from django.http import HttpResponseRedirect
from django.dispatch import receiver
from django.urls import reverse
import logging
import json

from orcaserver.forms import ProjectForm
from orcaserver.models import(Scenario, Project, Injectable,
                              InjectableConversionError)
from orcaserver.management import OrcaManager

logger = logging.getLogger('OrcaLog')
manager = OrcaManager()

def apply_injectables(orca, scenario):
    if not scenario:
        return
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        #  skip injectables which cannot be changed
        if not (inj.changed or inj.can_be_changed):
            continue
        try:
            converted_value = inj.validate_value()
        except InjectableConversionError as e:
            logger.warn(str(e))
            continue
        if inj.can_be_changed:
            orca.add_injectable(inj.name, converted_value)


class ProjectMixin:

    def get_project(self):
        """get the selected scenario"""
        project_pk = self.request.session.get('project')
        module = self.get_module()
        try:
            project = Project.objects.get(pk=project_pk, module=module)
        except Project.DoesNotExist:
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
        except Scenario.DoesNotExist:
            project_pk = self.request.session.get('project')
            scenarios = Scenario.objects.filter(project_id=project_pk)
            if scenarios:
                scenario = scenarios.first()
                self.request.session['scenario'] = scenario.pk
            else:
                scenario = None
        return scenario

    def get_orca(self):
        scenario = self.get_scenario()
        if not scenario:
            return
        orca = manager.get(scenario.id, create=False)
        if not orca:
            orca = manager.create(scenario.id, module=self.get_module())
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
    template_name = 'orcaserver/project.html'
    form_class = ProjectForm
    success_url = '/projects'

    def get(self, request, *args, **kwargs):
        self.project_id = kwargs.get('id')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.project_id = kwargs.get('id')
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['title'] = 'Change Project' if self.project_id else 'Add Project'
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['module'] = self.get_module()
        # ToDo: catch errors if project does not exist (maybe already
        # in get() or post())
        if self.project_id is not None:
            project = Project.objects.get(id=self.project_id)
            kwargs['project_name'] = project.name
            kwargs['project_description'] = project.description
            kwargs['init'] = project.init
        return kwargs

    def form_valid(self, form):
        fields = form.cleaned_data.copy()
        name = fields.pop('name')
        description = fields.pop('description')
        init = {}
        # additional fields are assumed to be injectable values
        for field, value in fields.items():
            init[field] = value
        if self.project_id is None:
            Project.objects.create(name=name, description=description,
                                   init=json.dumps(init),
                                   module=self.get_module())
        else:
            project = Project.objects.get(id=self.project_id)
            project.name = name
            project.description = description
            project.init = json.dumps(init)
            project.save()
        return super().form_valid(form)

class ExtractProjectView(ProjectMixin, FormView):
    ''''''

