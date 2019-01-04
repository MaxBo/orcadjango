from collections import OrderedDict
from django.http import HttpResponse
from django.template import loader
from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin, BaseFormView
import orca
from orcaserver.models import Injectable, Scenario
from orcaserver.forms import InjectableValueForm, InjectablesPopulateForm


@orca.injectable()
def inj1():
    return 'INJ 1'


@orca.injectable()
def inj2():
    return 'INJ 2'


def index(request):
    template = loader.get_template('orcaserver/index.html')
    return HttpResponse(template.render({}, request))

class ScenarioMixin:
    _backup = {}

    def get_scenario(self):
        """get the selected scenario"""
        scenario_pk = self.request.session.get('scenario')
        scenario = Scenario.objects.get(pk=scenario_pk)
        return scenario

    def backup_and_set_value(self, name, new_value):
        #  backup original value
        if not name in self._backup:
            self._backup[name] = orca.get_raw_injectable(name)
        # set to new value
        orca.add_injectable(name, new_value)


class InjectablesView(BaseFormView, ListView, ScenarioMixin):
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


class InjectableView(FormView, ScenarioMixin):
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
