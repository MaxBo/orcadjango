import orca
from django.views.generic import ListView
from orcaserver.models import Scenario, Injectable, Step
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse


class ScenarioMixin:
    _backup = {}

    def get_scenario(self):
        """get the selected scenario"""
        scenario_pk = self.request.session.get('scenario')
        try:
            scenario = Scenario.objects.get(pk=scenario_pk,
                                            module=orca._python_module)
        except Scenario.DoesNotExist:
            scenario = None
        return scenario

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        scenario = self.get_scenario()
        kwargs['scenario_name'] = scenario.name if scenario else 'none'
        kwargs['python_module'] = orca._python_module
        return kwargs


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
        inj.save()

    deleted_injectables = Injectable.objects.filter(scenario=scenario).\
        exclude(name__in=injectable_list)
    deleted_injectables.delete()


def create_steps(scenario):
    for name in orca.list_steps():
        Step.objects.create(name=name, scenario=scenario)


class ScenariosView(ScenarioMixin, ListView):
    model = Scenario
    template_name = 'orcaserver/scenarios.html'
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Return the injectables with their values."""
        scenarios = Scenario.objects.filter(module=orca._python_module)
        return scenarios

    def post(self, request, *args, **kwargs):
        scenario_id = request.POST.get('scenario')
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
            module = orca._python_module
            scenario = Scenario.objects.create(name=name, module=module)
            create_injectables(scenario)
            if request.POST.get('clone'):
                #  clone injectables and steps
                old_scenario_id = request.session.get('scenario')
                if old_scenario_id is None:
                    return HttpResponseBadRequest('No Scenario selected yet that could be cloned')
                old_scenario = Scenario.objects.get(pk=old_scenario_id,
                                                    module=module)

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
