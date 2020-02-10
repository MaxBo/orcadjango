from django.views.generic import ListView
from django.views.generic.edit import FormView
import orca
import numpy as np
from collections import OrderedDict
from orcaserver.views import ProjectMixin
from orcaserver.models import Injectable
from orcaserver.forms import InjectableValueForm
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse


class InjectablesView(ProjectMixin, ListView):
    model = Injectable
    template_name = 'orcaserver/injectables.html'
    context_object_name = 'grouped_injectables'

    def get_queryset(self):
        """Return the injectables with their values."""
        scenario = self.get_scenario()
        inj = orca.list_injectables()
        injectables = Injectable.objects.filter(name__in=inj,
                                                scenario=scenario)\
            .order_by('groupname', 'name')

        groups = sorted(set(injectables.values_list('groupname', flat=True)))
        grouped = OrderedDict()
        for group in groups:
            grouped[group] = injectables\
                .filter(groupname=group)\
                .order_by('order', 'name')
        return grouped

    def post(self, request, *args, **kwargs):
        if request.POST.get('reset'):
            qs = self.get_queryset()
            for group, injectables in qs.items():
                for inj in injectables:
                    if inj.can_be_changed:
                        orig_value = orca._injectable_backup[inj.name]
                    else:
                        orig_value = orca.get_injectable(inj.name)
                    inj.value = orig_value
                    inj.save()
                    if inj.can_be_changed:
                        orca.add_injectable(inj.name, orig_value)
        return HttpResponseRedirect(request.path_info)


class InjectableView(ProjectMixin, FormView):
    template_name = 'orcaserver/injectable.html'
    form_class = InjectableValueForm

    @property
    def name(self):
        return self.kwargs.get('name')

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        inj = Injectable.objects.get(name=self.name,
                                     scenario=self.get_scenario())
        return {'value': inj.value, }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        inj = Injectable.objects.get(name=self.name,
                                     scenario=self.get_scenario())
        kwargs['injectable'] = inj
        return kwargs

    def post(self, request, *args, **kwargs):
        inj = Injectable.objects.get(name=self.name,
                                     scenario=self.get_scenario())
        if not inj.can_be_changed:
            return HttpResponse(status=403)

        if request.POST.get('change'):
            return super().post(request, *args, **kwargs)

        if request.POST.get('reset'):
            inj.value = orca._injectable_backup[inj.name]
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
        kwargs['injectable'] = Injectable.objects.get(
            name=self.name, scenario=self.get_scenario())
        return kwargs

    def form_valid(self, form):
        inj: Injectable = Injectable.objects.get(name=self.name,
                                                 scenario=self.get_scenario())
        new_value = form.cleaned_data.get('value')
        inj.value = new_value
        if new_value != inj.value:
            inj.changed = True
        inj.valid = True
        inj.save()
        orca.add_injectable(inj.name, new_value)
        redirect = self.request.GET.get('next', reverse('injectables'))
        return HttpResponseRedirect(redirect)





