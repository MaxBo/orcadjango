import ast
import logging
import json
from django.views.generic import TemplateView
from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponseNotFound
import channels.layers
from asgiref.sync import async_to_sync
import orca

from orcaserver.threading import OrcaManager
from orcaserver.views import ProjectMixin
from orcaserver.models import Step, Injectable, Scenario
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
import json


class ScenarioHandler(logging.StreamHandler):
    def __init__(self, scenario,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenario = scenario

    def emit(self, record):
        channel_layer = channels.layers.get_channel_layer()
        group = f'log_{self.scenario.id}'
        async_to_sync(channel_layer.group_send)(group, {
            'message': record.message,
            'type': 'log_message'
        })

def apply_injectables(scenario):
    names = orca.list_injectables()
    injectables = Injectable.objects.filter(name__in=names, scenario=scenario)
    for inj in injectables:
        #  skip injectables which cannot be changed
        if not (inj.changed or inj.can_be_changed):
            continue
        #  get original type of injectable value (if not available, use string)
        original_type = type(orca._injectable_backup.get(inj.name, str))
        # compare to evaluation or value
        if inj.value is None:
            func = orca._injectable_function.get(inj.name)
            if func:
                converted_value = func()
            else:
                converted_value = orca.get_injectable(inj.name)
        elif issubclass(original_type, str):
            converted_value = inj.value
        else:
            try:
                converted_value = ast.literal_eval(inj.value)
                if not isinstance(converted_value, original_type):
                    #  try to cast the value using the original type
                    converted_value = original_type(inj.value)
            except (SyntaxError, ValueError) as e:

                # if casting does not work, raise warning
                # and use original value
                msg = (f'Injectable `{inj.name}` with value `{inj.value}` '
                       f'could not be casted to type `{original_type}`.'
                       f'Injectable Value was not overwritten.'
                       f'Error message: {repr(e)}')
                orca.logger.warning(msg)
                continue
        orca.add_injectable(inj.name, converted_value)


class StepsView(ProjectMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    @property
    def id(self):
        return self.kwargs.get('id')

    def get_context_data(self, **kwargs):
        scenario = self.get_scenario()
        steps_grouped = {}
        for name in orca.list_steps():
            wrapper = orca.get_step(name)
            group = wrapper.groupname or '-'
            steps_grouped.setdefault(group, []).append({
                'name': name,
                'description': wrapper._func.__doc__,
            })
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
        if scenario_id is None:
            return HttpResponseNotFound('scenario not found')
        scenario = Scenario.objects.get(id=scenario_id)
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        steps_json = []
        injectables_available = orca.list_injectables()
        for step in steps_scenario:
            func = orca.get_step(step.name)
            inj_names = func._func.__code__.co_varnames
            injectables = []
            for name in inj_names:
                if name not in injectables_available:
                    continue
                inj = Injectable.objects.get(name=name, scenario=scenario)
                injectables.append({
                    'id': inj.id,
                    'name': name,
                    'value': inj.value,
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
                'injectables': injectables
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
        manager = OrcaManager()
        status = {
            'running': manager.is_running,
            'last_user': manager.user,
            'last_start': manager.start_time,
        }
        return JsonResponse(status)

    @classmethod
    def run(cls, request):
        scenario_id = request.session.get('scenario')
        if not scenario_id:
            return
        scenario = Scenario.objects.get(id=scenario_id)
        message = f'Running Steps for scenario "{scenario.name}"'

        logger = logging.getLogger('OrcaLog')
        logger.addHandler(ScenarioHandler(scenario))
        logger.setLevel(logging.DEBUG)
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
        if manager.is_running:
            return
        manager.start(steps=steps, logger=logger,
                      user=request.user)
        return HttpResponse(status=200)

    @classmethod
    def abort(cls, request):
        manager = OrcaManager()
        manager.abort()
        return HttpResponse(status=200)