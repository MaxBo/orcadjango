from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.conf import settings
from collections import OrderedDict
import json

from orcaserver.views import ProjectMixin, recreate_injectables
from orcaserver.injectables import Injectable
from orcaserver.forms import InjectableValueForm
from orcaserver.management import OrcaManager, parse_injectables

manager = OrcaManager()


class InjectablesView(ProjectMixin, ListView):
    model = Injectable
    template_name = 'orcaserver/injectables.html'
    context_object_name = 'grouped_injectables'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        if not project:
            return HttpResponseRedirect(reverse('projects'))
        scenario = self.get_scenario()
        if not scenario:
            return HttpResponseRedirect(reverse('scenarios'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['show_status'] = True
        kwargs['debug'] = settings.DEBUG
        return kwargs

    def get_queryset(self):
        """Return the injectables with their values."""
        scenario = self.get_scenario()
        if not scenario:
            return []
        orca = self.get_orca()
        injectables = parse_injectables(orca)
        scen_injectables = Injectable.objects.filter(
            name__in=injectables.keys(), scenario=scenario)
        grouped = {}
        # enrich injectables in scenario with meta data
        for inj in scen_injectables:
            meta = injectables[inj.name]
            inj.docstring = meta['docstring']
            inj.order = meta.get('order', 10000)
            group = meta.get('group', '')
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(inj)
        for group, inj_list in grouped.items():
            grouped[group] = sorted(inj_list, key = lambda i: (i.order, i.name))

        grouped = OrderedDict(sorted(grouped.items()))
        return grouped

    def post(self, request, *args, **kwargs):
        scenario = self.get_scenario()
        manager = OrcaManager()
        is_running = manager.is_running(scenario.id)
        if is_running:
            return HttpResponse(content='Injectables can not be changed while '
                                'the scenario is running', status=400)
        # reset orca
        manager.remove(scenario.id)
        orca = self.get_orca(scenario)
        if request.POST.get('reset'):
            Injectable.objects.filter(scenario=scenario).delete()
            recreate_injectables(orca, scenario)
        if request.POST.get('refresh'):
            recreate_injectables(orca, scenario, keep_values=True)
        return HttpResponseRedirect(request.path_info)


class InjectableView(ProjectMixin, FormView):
    template_name = 'orcaserver/injectable.html'
    form_class = InjectableValueForm

    @property
    def name(self):
        return self.kwargs.get('name')

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        try:
            inj = Injectable.objects.get(name=self.name,
                                         scenario=self.get_scenario())
            kwargs['injectable'] = inj
        except ObjectDoesNotExist:
            kwargs['error_message'] = (
                'Injectable not found. Your project seems not to be up to date '
                'with the module. Please synchronize the parameters '
                '(parameters page).')
            kwargs['injectable'] = None
        form = kwargs['form']
        meta = inj.meta
        if not meta:
            kwargs['error_message'] = (
                'Injectable does not exist anymore. Please synchronize the '
                'parameters (parameters page).')
            kwargs.pop('injectable')
        else:
            kwargs['docstring'] = meta['docstring']
            if not form.is_valid():
                errors = form.errors.get('value', [])
                kwargs['error_message'] = kwargs.get('error_message', []) + errors
        return kwargs

    def post(self, request, *args, **kwargs):
        inj = Injectable.objects.get(name=self.name,
                                     scenario=self.get_scenario())
        if not inj.can_be_changed:
            return HttpResponse(status=403)

        if request.POST.get('change'):
            return super().post(request, *args, **kwargs)

        if request.POST.get('reset'):
            orca = self.get_orca()
            init = json.loads(inj.scenario.project.init)
            inj.value = init.get(inj.name, orca._injectable_backup[inj.name])
            inj.save()
            orca.add_injectable(inj.name, inj.value)
            return HttpResponseRedirect(request.path_info)

        elif request.POST.get('clear'):
            inj.value = None
            inj.save()

        redirect = request.GET.get('next', reverse('injectables'))
        return HttpResponseRedirect(redirect)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs['injectable'] = Injectable.objects.get(
                name=self.name, scenario=self.get_scenario())
        except ObjectDoesNotExist:
            kwargs['injectable'] = None
        return kwargs

    def form_valid(self, form):
        scenario = self.get_scenario()
        orca = self.get_orca()
        inj = Injectable.objects.get(name=self.name,
                                     scenario=scenario)
        value = form.cleaned_data.get('value')
        inj.valid = True
        inj.value = value
        inj.save()
        orca.add_injectable(inj.name, value)
        redirect = self.request.GET.get('next', reverse('injectables'))
        return HttpResponseRedirect(redirect)
