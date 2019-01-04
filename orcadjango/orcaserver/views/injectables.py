from collections import OrderedDict
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin, BaseFormView
import orca
from orcaserver.models import Injectables
from orcaserver.forms import InjectableValueForm, InjectablesPopulateForm


@orca.injectable()
def inj1():
    return 'INJ 1'


@orca.injectable()
def inj2():
    return 'INJ 2'


def index(request):
    return HttpResponse("Hello, world. You're at the index.")


class InjectablesView(BaseFormView, ListView):
    model = Injectables
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
        if action == 'Populate':
            #  enter to model
            for name in orca.list_injectables():
                value = orca.get_injectable(name)
                inj = Injectables.objects.get_or_create(name=name,
                                                        value=value,
                                                        changed=False)
        return super().form_valid(form)


class InjectableView(FormView):
    template_name = 'orcaserver/injectable.html'
    form_class = InjectableValueForm
    success_url = '/orca/injectables'
    _backup = {}

    @property
    def name(self):
        return self.kwargs.get('name')

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        value = orca.get_injectable(self.name)
        return {'value': value, }

    def form_valid(self, form):
        action = self.request.POST.get('action')
        if action == 'Change':
            #  backup original value
            if not self.name in self._backup:
                self._backup[self.name] = orca.get_raw_injectable(self.name)
            # set to new value
            value = form.cleaned_data.get('value')
            orca.add_injectable(self.name, value)
            inj = Injectables.objects.get(name=self.name)
            inj.value = value
            inj.changed = True
            inj.save
        elif action == 'Reset':
            # reset to backup
            wrapper = self._backup.get(self.name)
            if wrapper:
                orca.add_injectable(self.name,
                                    value=wrapper._func,
                                    cache=wrapper.cache,
                                    cache_scope=wrapper.cache_scope)
            inj = Injectables.objects.get(name=self.name)
            inj.value = orca.get_injectable(self.name)
            inj.changed = False
            inj.save
        return super().form_valid(form)
