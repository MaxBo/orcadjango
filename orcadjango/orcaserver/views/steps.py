import logging
import json
from inspect import signature
from django.views.generic import TemplateView
from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponseNotFound
from collections import OrderedDict

from orcaserver.management import OrcaManager
from orcaserver.views import ProjectMixin, apply_injectables
from orcaserver.models import Step, Injectable, Scenario
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
import json

logger = logging.getLogger('OrcaLog')
manager = OrcaManager()


class StepsView(ProjectMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    @property
    def id(self):
        return self.kwargs.get('id')

    def get(self, request, *args, **kwargs):
        if not self.get_scenario():
            return  HttpResponseRedirect(reverse('scenarios'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        scenario = self.get_scenario()
        orca = manager.get(scenario.id)
        steps_grouped = OrderedDict()
        for name in orca.list_steps():
            wrapper = orca.get_step(name)
            group = getattr(wrapper, 'groupname', '-')
            order = getattr(wrapper, 'order', 1)
            steps_grouped.setdefault(group, []).append({
                'name': name,
                'description': wrapper._func.__doc__ or '',
                'order': order,
                'module': wrapper._func.__module__,
            })
        # order the steps inside the groups
        for group, steps_group in steps_grouped.items():
            steps_grouped[group] = sorted(steps_group, key=lambda x: x['order'])

        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        kwargs = super().get_context_data(**kwargs)
        kwargs['steps_available'] = steps_grouped if scenario else []
        kwargs['steps_scenario'] = steps_scenario
        return kwargs

    @staticmethod
    def list(request):
        if request.method == 'POST':
            body = json.loads(request.body)
            for item in body:
                step = Step.objects.get(id=item['id'])
                step.order = item['order']
                step.save()
        scenario_id = request.session.get('scenario')
        orca = manager.get(scenario_id)
        if scenario_id is None:
            return HttpResponseNotFound('scenario not found')
        scenario = Scenario.objects.get(id=scenario_id)
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        steps_json = []
        injectables_available = orca.list_injectables()
        for step in steps_scenario:
            func = orca.get_step(step.name)
            sig = signature(func._func)
            inj_parameters = sig.parameters
            injectables = []
            for name in inj_parameters:
                if name not in injectables_available:
                    continue
                inj = Injectable.objects.get(name=name, scenario=scenario)
                injectables.append({
                    'id': inj.id,
                    'name': name,
                    'value': repr(inj.value),
                    'url': f"{reverse('injectables')}{name}",
                })
            started = step.started
            finished = step.finished
            if started:
                started = started.strftime("%a %b %d %H:%M:%S %Z %Y")
            if finished:
                finished = finished.strftime("%a %b %d %H:%M:%S %Z %Y")
            steps_json.append({
                'id': step.id,
                'name': step.name,
                'started': started,
                'finished': finished,
                'success': step.success,
                'order': step.order,
                'is_active': step.active,
                'injectables': injectables,
                'module': func._func.__module__,
            })
        return JsonResponse(steps_json, safe=False)

    def post(self, request, *args, **kwargs):
        scenario = self.get_scenario()
        if request.POST.get('add'):
            steps = request.POST.get('steps', '').split(',')
            for step in steps:
                if not step:
                    continue
                Step.objects.create(scenario=scenario,
                                    name=step, order=10000)
        elif request.POST.get('remove'):
            step_id = request.POST.get('step')
            step = Step.objects.get(id=step_id)
            step.delete()
        elif request.POST.get('run'):
            pass
        return HttpResponseRedirect(request.path_info)

    # to do for updating is_active
    @staticmethod
    def detail(request, *args, **kwargs):
        step_id = kwargs.get('id')
        if request.method == 'PATCH':
            try:
                step = Step.objects.get(id=step_id)
            except ObjectDoesNotExist:
                return JsonResponse({}, safe=False)
            body = json.loads(request.body)
            is_active = body.get('is_active')
            step.active = is_active
            step.save()
            return JsonResponse({}, safe=False)

    @classmethod
    def status(cls, request):
        #manager = OrcaManager()
        #status_text = f'currently run by user "{manager.user}"'\
            #if manager.is_running else 'not in use'
        status = {
            'running': '',# manager.is_running,
            'text': '', # status_text,
            'last_user': '', # manager.user,
            'last_start': '' # manager.start_time,
        }
        return JsonResponse(status)

    @classmethod
    def run(cls, request):
        scenario_id = request.session.get('scenario')
        if not scenario_id:
            return
        scenario = Scenario.objects.get(id=scenario_id)
        message = f'Running Steps for scenario "{scenario.name}"'

        logger.info(message)

        active_steps = Step.objects.filter(scenario=scenario, active=True)
        steps = active_steps.order_by('order')
        for step in steps:
            step.started = None
            step.finished = None
            step.success = False
            step.save()
        apply_injectables(scenario)
        manager = OrcaManager()
        if manager.is_running(scenario.id):
            return HttpResponse(status=400)
        manager.start(scenario.id, steps=steps, user=request.user)
        return HttpResponse(status=200)

    @classmethod
    def abort(cls, request):
        manager = OrcaManager()
        manager.abort()
        return HttpResponse(status=200)


class StatusView(ProjectMixin, TemplateView):
    template_name = 'orcaserver/status.html'
