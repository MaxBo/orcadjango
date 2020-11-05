from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from collections import OrderedDict

from orcaserver.views import ProjectMixin
from orcaserver.models import Injectable
from orcaserver.forms import InjectableValueForm
from orcaserver.management import OrcaManager

manager = OrcaManager()


class InjectablesView(ProjectMixin, ListView):
    model = Injectable
    template_name = 'orcaserver/injectables.html'
    context_object_name = 'grouped_injectables'

    def get_queryset(self):
        """Return the injectables with their values."""
        scenario = self.get_scenario()
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
        orca = self.get_orca()
        if request.POST.get('reset'):
            qs = self.get_queryset()
            for group, injectables in qs.items():
                for inj in injectables:  # type: Injectable
                    if inj.can_be_changed:
                        orig_value = orca._injectable_backup[inj.name]
                    else:
                        try:
                            orig_value = orca.get_injectable(inj.name)
                            _ = inj.validate_value(orig_value)
                        except Exception as e:
                            orig_value = str(e)
                            inj.valid = False
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
        try:
            inj = Injectable.objects.get(name=self.name,
                                         scenario=self.get_scenario())
            return {'value': inj.value}
        except ObjectDoesNotExist:
            return {'value': None}

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        try:
            inj = Injectable.objects.get(name=self.name,
                                         scenario=self.get_scenario())
            kwargs['injectable'] = inj
        except ObjectDoesNotExist:
            kwargs['error_message'] = (
                'Injectable not found. Your project seems not to be up to date '
                'with the module. Please refresh the injectables '
                '(scenario page)!')
            kwargs['injectable'] = None
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
        try:
            kwargs['injectable'] = Injectable.objects.get(
                name=self.name, scenario=self.get_scenario())
        except ObjectDoesNotExist:
            kwargs['injectable'] = None
        return kwargs

    def form_valid(self, form):
        scenario = self.get_scenario()
        orca = self.get_orca()
        inj: Injectable = Injectable.objects.get(name=self.name,
                                                 scenario=scenario)
        new_value = form.cleaned_data.get('value')
        inj.value = new_value
        if new_value != inj.value:
            inj.changed = True
        inj.valid = True
        inj.save()
        orca.add_injectable(inj.name, new_value)
        redirect = self.request.GET.get('next', reverse('injectables'))
        return HttpResponseRedirect(redirect)





