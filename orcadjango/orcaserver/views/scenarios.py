import orca
from django.views.generic import ListView
from orcaserver.models import Scenario, Injectable, Step
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
from orcaserver.views import ProjectMixin


overwritable_types = (str, bytes, int, float, complex,
                      tuple, list, dict, set, bool, None.__class__)


def create_injectables(scenario):
    injectable_list = orca.list_injectables()
    for name in injectable_list:
        inj, created = Injectable.objects.get_or_create(name=name,
                                                        scenario=scenario)
        value = orca._injectable_backup.get(name)
        #  check if the original type is overwritable
        inj.can_be_changed = isinstance(value, overwritable_types)
        if created:
            # for new injectables, set the initial value
            inj.value = value
        funcwrapper = orca._injectable_function.get(name)
        if isinstance(funcwrapper, orca.orca._InjectableFuncWrapper):
            inj.docstring = funcwrapper._func.__doc__
            inj.module = funcwrapper._func.__module__
            inj.groupname = getattr(funcwrapper, 'groupname', None)
        inj.save()

    deleted_injectables = Injectable.objects.filter(scenario=scenario).\
        exclude(name__in=injectable_list)
    deleted_injectables.delete()


def create_steps(scenario):
    for name in orca.list_steps():
        Step.objects.create(name=name, scenario=scenario)


class ScenariosView(ProjectMixin, ListView):
    model = Scenario
    template_name = 'orcaserver/scenarios.html'
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Return the injectables with their values."""
        project = self.request.session.get('project')
        scenarios = Scenario.objects.filter(project=project)
        return scenarios

    def post(self, request, *args, **kwargs):
        scenario_id = request.POST.get('scenario')
        if scenario_id:
            if request.POST.get('select'):
                self.request.session['scenario'] = int(scenario_id)
            elif request.POST.get('delete'):
                Scenario.objects.get(id=scenario_id).delete()
            elif request.POST.get('refresh'):
                scenario = Scenario.objects.get(id=scenario_id)
                create_injectables(scenario)
        return HttpResponseRedirect(request.path_info)

    def create(request):
        if request.method == 'POST':
            name = request.POST.get('name')
            if not name:
                return HttpResponseBadRequest('name can not be empty')
            project_pk = request.session.get('project')
            scenario = Scenario.objects.create(name=name, project_id=project_pk)
            create_injectables(scenario)
            if request.POST.get('clone'):
                #  clone injectables and steps
                old_scenario_id = request.session.get('scenario')
                if old_scenario_id is None:
                    return HttpResponseBadRequest('No Scenario selected yet that could be cloned')
                old_scenario = Scenario.objects.get(pk=old_scenario_id)

                # copy injectable values
                injectables = Injectable.objects.filter(scenario=old_scenario)
                for inj in injectables:
                    new_inj, created = Injectable.objects.get_or_create(
                        scenario=scenario,
                        name=inj.name)
                    new_inj.value = inj.value
                    new_inj.changed = inj.changed
                    new_inj.docstring = inj.docstring
                    new_inj.module = inj.module
                    new_inj.save()

                # copy steps
                steps = Step.objects.filter(scenario=old_scenario)
                for step in steps:
                    new_step, created = Step.objects.get_or_create(
                        scenario=scenario,
                        name=step.name)
                    new_step.order = step.order
                    new_step.save()

            request.session['scenario'] = scenario.id
        return HttpResponseRedirect(reverse('scenarios'))
