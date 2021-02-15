from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from collections import OrderedDict
import json

from orcaserver.views import ProjectMixin, recreate_injectables
from orcaserver.models import Injectable
from orcaserver.forms import InjectableValueForm
from orcaserver.management import OrcaManager

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
        return kwargs

    def get_queryset(self):
        """Return the injectables with their values."""
        scenario = self.get_scenario()
        if not scenario:
            return []
        orca = self.get_orca()
        inj = orca.list_injectables()
        injectables = Injectable.objects.filter(name__in=inj,
                                                scenario=scenario)\
            .order_by('groupname', 'name')

        groups = sorted(set(injectables.values_list('groupname', flat=True)))
        grouped = {}
        for group in groups:
            grouped[group] = injectables\
                .filter(groupname=group)\
                .order_by('order', 'name')
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





