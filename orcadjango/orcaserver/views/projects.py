import orca
from django.views.generic import ListView
from django.contrib.gis import forms
# from orcaserver.models import Scenario, Injectable, Step
#from django.http import HttpResponseRedirect, HttpResponseBadRequest
#from django.urls import reverse


from orcaserver.models import Scenario, Project, GeoProject


class ProjectMixin:
    _backup = {}

    def get_project(self):
        """get the selected scenario"""
        project_pk = self.request.session.get('project')
        try:
            project = Project.objects.get(pk=project_pk)
        except Project.DoesNotExist:
            project = None
        return project

    def get_scenario(self):
        """get the selected scenario"""
        scenario_pk = self.request.session.get('scenario')
        try:
            scenario = Scenario.objects.get(pk=scenario_pk)
        except Scenario.DoesNotExist:
            scenario = None
        return scenario

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        project = self.get_project()
        scenario = self.get_scenario()
        kwargs['project_name'] = project.name if scenario else 'none'
        kwargs['scenario_name'] = scenario.name if scenario else 'none'
        kwargs['python_module'] = orca._python_module
        return kwargs


class ProjectView(ProjectMixin, ListView):
    model = Project
    template_name = 'orcaserver/projects.html'
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Return the injectables with their values."""
        projects = self.model.objects.filter(module=orca._python_module)
        return projects


class GeoProjectView(ProjectView):
    model = GeoProject
    template_name = 'orcaserver/geoprojects.html'