from django.views.generic import ListView
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse
import json
from django.core.exceptions import ObjectDoesNotExist

from orcaserver.views import ProjectMixin
from orcaserver.management import OrcaManager,
from orcaserver.models import Scenario, Step
from orcaserver.injectables import Injectable

overwritable_types = (str, bytes, int, float, complex,
                      tuple, list, dict, set, bool, None.__class__)


class ScenariosView(ProjectMixin, ListView):
    model = Scenario
    template_name = 'orcaserver/scenarios.html'
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Return the injectables with their values."""
        project = self.request.session.get('project')
        scenarios = Scenario.objects.filter(project=project).order_by('name')
        return scenarios

    def post(self, request, *args, **kwargs):
        if request.POST.get('create'):
            self.create(request)
        elif request.POST.get('clone'):
            self.create(request, clone=True)
        else:
            scenario_id = request.POST.get('scenario')
            if scenario_id:
                if request.POST.get('select'):
                    self.request.session['scenario'] = int(scenario_id)
                    scenario = Scenario.objects.get(pk=scenario_id)
                    orca = self.get_orca()
                    apply_injectables(orca, scenario)
                    return HttpResponseRedirect(reverse('injectables'))
                elif request.POST.get('delete'):
                    try:
                        OrcaManager().remove(scenario_id)
                    except Exception as e:
                        return HttpResponseBadRequest(content=str(e))
                    Scenario.objects.get(id=scenario_id).delete()
                elif request.POST.get('reset'):
                    scenario = Scenario.objects.get(id=scenario_id)
                    orca = self.get_orca()
                    recreate_injectables(orca, scenario)
        return HttpResponseRedirect(request.path_info)

    def create(self, request, clone=False):
        name = request.POST.get('name')
        if not name:
            return HttpResponseBadRequest('name can not be empty')
        project = self.get_project()
        scenario = Scenario.objects.create(name=name, project=project)
        orca = self.get_orca()
        recreate_injectables(orca, scenario)

        if clone:
            #  clone injectables and steps
            old_scenario_id = request.session.get('scenario')
            if old_scenario_id is None:
                return HttpResponseBadRequest('No Scenario selected yet that could be cloned')
            old_scenario = Scenario.objects.get(pk=old_scenario_id)

            # copy injectable values
            injectables = Injectable.objects.filter(scenario=old_scenario)
            for inj in injectables:
                new_inj, created = Injectable.objects.get_or_create(
                    scenario=scenario, name=inj.name)
                new_inj.value = inj.value
                new_inj.save()

            # copy steps
            steps = Step.objects.filter(scenario=old_scenario)
            for step in steps:
                new_step, created = Step.objects.get_or_create(
                    scenario=scenario,
                    name=step.name)
                new_step.order = step.order
                new_step.save()

        request.session['scenario'] = int(scenario.id)