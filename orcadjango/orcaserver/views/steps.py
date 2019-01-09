from collections import OrderedDict
from django.views.generic import ListView
from django.views.generic.edit import BaseFormView
from django.shortcuts import render, HttpResponseRedirect
import orca
from orcaserver.views import ScenarioMixin
from orcaserver.models import Step
from orcaserver.forms import StepsPopulateForm, StepsForm


class StepsView(ScenarioMixin, BaseFormView, ListView):
    model = Step
    template_name = 'orcaserver/steps.html'
    context_object_name = 'step_dict'
    form_class = StepsPopulateForm
    success_url = '/steps'

    def get_queryset(self):
        """Return the steps with their values."""
        qs = OrderedDict(((name, orca.get_step(name))
                          for name in orca.list_steps()))
        return qs

    def form_valid(self, form):
        action = self.request.POST.get('action')
        scenario = self.get_scenario()
        if action == 'Populate':
            #  enter to model
            for name in orca.list_steps():
                step, created = Step.objects.get_or_create(
                    name=name,
                    scenario=scenario)
                step.value = orca.get_step(name)
                step.changed = False
                step.save()
        if action == 'Save':
            #  save values for scenario
            for name in orca.list_steps():
                step, created = Step.objects.get_or_create(
                    name=name,
                    scenario=scenario)
                step.value = orca.get_step(name)
                step.save()

        if action == 'Load':
            #  save values for scenario
            for name in orca.list_steps():
                step, created = Step.objects.get_or_create(
                    name=name,
                    scenario=scenario)
        if action == 'Run':
            steps = form.cleaned_data['steps']
            orca.run(steps)
            return HttpResponseRedirect('/steps')

        return super().form_valid(form)
