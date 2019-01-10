from django.views.generic import ListView
from orcaserver.models import Scenario, Injectable
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
import orca
import os


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

def create_injectables(scenario):
    for inj in orca.list_injectables():
        value = orca.get_injectable(inj)
        Injectable.objects.create(name=inj, value=value, scenario=scenario)


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
            self.request.session['scenario'] = scenario_id
        elif request.POST.get('delete'):
            Scenario.objects.get(id=scenario_id).delete()
        return HttpResponseRedirect(request.path_info)

    def create(request):
        if request.method == 'POST':
            name = request.POST.get('name')
            if not name:
                return HttpResponseBadRequest('name can not be empty')
            module = orca._python_module
            scenario = Scenario.objects.create(name=name, module=module)
            request.session['scenario'] = scenario.id
            create_injectables(scenario)
        return HttpResponseRedirect(reverse('scenarios'))
