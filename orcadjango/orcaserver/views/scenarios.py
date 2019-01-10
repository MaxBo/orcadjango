from django.views.generic import ListView
from orcaserver.models import Scenario
from orcaserver.forms import ScenarioForm
from orcaserver.views import ScenarioMixin
from django.views.generic.edit import BaseFormView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import HttpResponseBadRequest
import os


class ScenariosView(ScenarioMixin, ListView):
    model = Scenario
    template_name = 'orcaserver/scenarios.html'
    context_object_name = 'scenarios'

    def post(self, request, *args, **kwargs):
        scenario_id = request.POST.get('scenario')
        if request.POST.get('select'):
            self.request.session['scenario'] = scenario_id
        elif request.POST.get('delete'):
            Scenario.objects.get(id=scenario_id).delete()
        return HttpResponseRedirect(request.path_info)

    def create(request):
        if request.method == 'POST':
            name = request.POST.get('name')
            if not name:
                return HttpResponseBadRequest('name can not be empty')
            scenario = Scenario.objects.create(name=name)
            request.session['scenario'] = scenario.id
        return HttpResponseRedirect(reverse('scenarios'))
