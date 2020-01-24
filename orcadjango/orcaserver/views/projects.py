import orca
from django.views.generic import ListView
from django.http import HttpResponseRedirect
from django.db.models.signals import post_save
from django.dispatch import receiver

from orcaserver.models import Scenario, Project, GeoProject

@receiver(post_save, sender=GeoProject)
@receiver(post_save, sender=Project)
def create_project(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if created:
        instance.module = orca._python_module
        instance.save()


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
        kwargs['active_project'] = project
        kwargs['active_scenario'] = scenario
        kwargs['python_module'] = orca._python_module
        kwargs['show_project_settings'] = True
        return kwargs


class ProjectView(ProjectMixin, ListView):
    model = Project
    template_name = 'orcaserver/projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        """Return the injectables with their values."""
        projects = self.model.objects.filter(module=orca._python_module)
        return projects

    def post(self, request, *args, **kwargs):
        project_id = request.POST.get('project')
        if project_id:
            if request.POST.get('select'):
                self.request.session['project'] = int(project_id)
                self.request.session['scenario'] = None
            elif request.POST.get('delete'):
                Project.objects.get(id=project_id).delete()
        return HttpResponseRedirect(request.path_info)


class GeoProjectView(ProjectView):
    model = GeoProject
    template_name = 'orcaserver/geoprojects.html'