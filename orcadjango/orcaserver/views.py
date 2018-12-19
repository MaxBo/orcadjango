import os
from collections import OrderedDict
from django.shortcuts import render, HttpResponseRedirect
from django.template import loader
from django.views import generic
from django.views.generic.edit import FormView
import orca
from .models import Injectables
from .forms import InjectableValueForm

@orca.injectable()
def inj1():
    return 'INJ 1'

@orca.injectable()
def inj2():
    return 'INJ 2'


from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the index.")


class InjectablesView(generic.ListView):
    template_name = 'orcaserver/injectables.html'
    context_object_name = 'injectable_dict'

    def get_queryset(self):
        """Return the injectables with their values."""
        qs = OrderedDict(((name, orca.get_injectable(name))
                          for name in orca.list_injectables()))
        return qs


class InjectableView(FormView):
    template_name = 'orcaserver/injectable.html'
    form_class = InjectableValueForm
    success_url = '/orca/injectables'

    @property
    def name(self):
        return self.kwargs.get('name')

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        value = orca.get_injectable(self.name)
        return {'value': value,}

    def form_valid(self, form):
        value = form.cleaned_data.get('value')
        orca.add_injectable(self.name, value)
        return super().form_valid(form)
