from collections import OrderedDict
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView
from django.shortcuts import render, HttpResponseRedirect
import orca
from orcaserver.views import ScenarioMixin
from orcaserver.models import Step, Injectable, Scenario
from django.urls import reverse

def apply_injectables(scenario):
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        orca.add_injectable(inj.name, inj.value)


class StepsView(ScenarioMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    def get_context_data(self, **kwargs):
        steps_available = OrderedDict(((name, orca.get_step(name))
                                       for name in orca.list_steps()))
        scenario = self.get_scenario()
        steps_scenario = Step.objects.filter(scenario=scenario)
        kwargs = super().get_context_data(**kwargs)
        kwargs['steps_available'] = steps_available
        kwargs['steps_scenario'] = steps_scenario
        return kwargs

    def post(self, request, *args, **kwargs):
        scenario_id = request.POST.get('scenario')
        if request.POST.get('add'):
            steps = request.POST.get('add_steps', '').split(',')
            scenario = self.get_scenario()
            for step in steps:
                if not step:
                    continue
                Step.objects.create(scenario=scenario,
                                    name=step, order=10000)
        elif request.POST.get('remove'):
            steps = request.POST.get('remove_steps', '').split(',')
            scenario = self.get_scenario()
            for step_id in steps:
                if not step_id:
                    continue
                step = Step.objects.get(id=step_id)
                step.delete()
        elif request.POST.get('run'):
            steps = form.cleaned_data['steps']
            apply_injectables(self.get_scenario())
            orca.run(steps)
        return HttpResponseRedirect(request.path_info)
