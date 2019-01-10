from collections import OrderedDict
from django.views.generic import ListView
from django.views.generic.edit import FormView, BaseFormView
import orca
from orcaserver.models import Injectable, Scenario
from orcaserver.forms import InjectableValueForm, InjectablesPopulateForm


class ScenarioMixin:
    _backup = {}

    def get_scenario(self):
        """get the selected scenario"""
        scenario_pk = self.request.session.get('scenario')
        try:
            scenario = Scenario.objects.get(pk=scenario_pk)
        except Scenario.DoesNotExist:
            scenario = None
        return scenario

    def backup_and_set_value(self, name, new_value):
        #  backup original value
        if name not in self._backup:
            self._backup[name] = orca.get_raw_injectable(name)
        # set to new value
        orca.add_injectable(name, new_value)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        scenario = self.get_scenario()
        kwargs['scenario_name'] = scenario.name if scenario else 'none'
        return kwargs


class InjectablesView(ScenarioMixin, BaseFormView, ListView):
    model = Injectable
    template_name = 'orcaserver/injectables.html'
    context_object_name = 'injectable_dict'
    form_class = InjectablesPopulateForm
    success_url = '/orca/injectables'

    def get_queryset(self):
        """Return the injectables with their values."""
        qs = OrderedDict(((name, orca.get_injectable(name))
                          for name in orca.list_injectables()))
        return qs

    def form_valid(self, form):
        action = self.request.POST.get('action')
        scenario = self.get_scenario()
        if action == 'Populate':
            #  enter to model
            for name in orca.list_injectables():
                inj, created = Injectable.objects.get_or_create(
                    name=name,
                    scenario=scenario)
                inj.value = orca.get_injectable(name)
                inj.changed = False
                inj.save()
        if action == 'Save':
            #  save values for scenario
            for name in orca.list_injectables():
                inj, created = Injectable.objects.get_or_create(
                    name=name,
                    scenario=scenario)
                inj.value = orca.get_injectable(name)
                inj.save()

        if action == 'Load':
            #  save values for scenario
            for name in orca.list_injectables():
                inj, created = Injectable.objects.get_or_create(
                    name=name,
                    scenario=scenario)
                self.backup_and_set_value(name, inj.value)

        return super().form_valid(form)


class InjectableView(ScenarioMixin, FormView):
    template_name = 'orcaserver/injectable.html'
    form_class = InjectableValueForm
    success_url = '/orca/injectables'

    @property
    def name(self):
        return self.kwargs.get('name')

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        value = orca.get_injectable(self.name)
        return {'value': value, }

    def form_valid(self, form):
        action = self.request.POST.get('action')
        scenario = self.get_scenario()
        if action == 'Change':
            new_value = form.cleaned_data.get('value')
            self.backup_and_set_value(self.name, new_value)
            inj = Injectable.objects.get(name=self.name,
                                         scenario=scenario)
            if new_value != inj.value:
                inj.changed = True
            inj.value = new_value
            inj.save
        elif action == 'Reset':
            # reset to backup
            wrapper = self._backup.get(self.name)
            if wrapper:
                orca.add_injectable(self.name,
                                    value=wrapper._func,
                                    cache=wrapper.cache,
                                    cache_scope=wrapper.cache_scope)
            inj = Injectable.objects.get(name=self.name,
                                         scenario=scenario)
            inj.value = orca.get_injectable(self.name)
            inj.changed = False
            inj.save
        return super().form_valid(form)
