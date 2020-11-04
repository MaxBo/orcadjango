from django.views.generic import ListView
from django.http import HttpResponseRedirect
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
import logging

from orcaserver.models import(Scenario, Project, GeoProject, Injectable,
                              InjectableConversionError)
from orcaserver.management import OrcaManager

logger = logging.getLogger('OrcaLog')
manager = OrcaManager()

@receiver(post_save, sender=GeoProject)
@receiver(post_save, sender=Project)
def create_project(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if created:
        instance.module = OrcaManager().python_module
        instance.save()

def apply_injectables(scenario):
    if not scenario:
        return
    orca = manager.get(scenario.id)
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
    _backup = {}

    def get_project(self):
        """get the selected scenario"""
        project_pk = self.request.session.get('project')
        try:
            project = Project.objects.get(pk=project_pk)
        except Project.DoesNotExist:
            projects = Project.objects.filter(module=settings.ORCA_MODULE)
            if projects:
                project = projects.first()
                self.request.session['project'] = project.pk
            else:
                project = None
        return project

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
        orca = manager.get(scenario.id, create=False)
        if not orca:
            orca = manager.create(scenario.id)
            apply_injectables(scenario)
        return orca

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        project = self.get_project()
        scenario = self.get_scenario()
        kwargs['active_project'] = project
        kwargs['active_scenario'] = scenario
        kwargs['python_module'] = OrcaManager().python_module
        kwargs['show_project_settings'] = True
        return kwargs


class ProjectView(ProjectMixin, ListView):
    model = Project
    template_name = 'orcaserver/projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """Return the injectables with their values."""
        projects = self.model.objects.filter(module=OrcaManager().python_module)
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


class GeoProjectView(ProjectView):
    model = GeoProject
    template_name = 'orcaserver/geoprojects.html'