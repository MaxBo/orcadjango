import json
from inspect import signature
from django.views.generic import TemplateView, ListView
from django.shortcuts import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse, HttpResponseNotFound
from collections import OrderedDict
from django.db.models import Max
from django.conf import settings
import json
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from dateutil import tz

from orcaserver.management import OrcaManager
from orcaserver.views import ProjectMixin, apply_injectables
from orcaserver.models import Step, Scenario, LogEntry, Run
from orcaserver.injectables import Injectable

manager = OrcaManager()


class StepsView(ProjectMixin, TemplateView):
    template_name = 'orcaserver/steps.html'

    @property
    def id(self):
        return self.kwargs.get('id')

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        if not project:
            return HttpResponseRedirect(reverse('projects'))
        scenario = self.get_scenario()
        if not scenario:
            return HttpResponseRedirect(reverse('scenarios'))
        #apply_injectables(scenario)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        scenario = self.get_scenario()
        orca = self.get_orca()
        steps_grouped = {}
        steps_available = orca.list_steps()
        meta = getattr(orca, 'meta', {})
        steps_meta = {}
        for name in steps_available:
            _meta = meta.get(name, {})
            wrapper = orca.get_step(name)
            group = _meta.get('group', '-')
            order = _meta.get('order', 1)
            required = _meta.get('required', [])
            if not isinstance(required, list):
                required = [required]
            required = [r.__name__ if callable(r) else str(r) for r in required]
            m = {
                'name': name,
                'description': wrapper._func.__doc__ or '',
                'order': order,
                'required': ', '.join(required),
            }
            steps_meta[name] = m
            steps_grouped.setdefault(group, []).append(m)
        # order the steps inside the groups
        for group, steps_group in steps_grouped.items():
            steps_grouped[group] = sorted(steps_group, key=lambda x: x['order'])

        steps_grouped = OrderedDict(sorted(steps_grouped.items()))
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        injectables_available = orca.list_injectables()
        for step in steps_scenario:
            if step.name not in steps_available:
                step.valid = False
                step.docstring = (
                    'Step not found. Your project seems not to be up to date '
                    'with the module. Please remove this step.')
                continue
            step.docstring = steps_meta[step.name]['description']
            step.required = steps_meta[step.name]['required']
            step.valid = True

            func = orca.get_step(step.name)
            sig = signature(func._func)
            inj_parameters = sig.parameters
            injectables = []
            for name in inj_parameters:
                if name not in injectables_available:
                    continue
                try:
                    inj = Injectable.objects.get(name=name, scenario=scenario)
                    meta = inj.meta
                    desc = inj.meta.get('docstring', '') if meta else ''
                    injectables.append({
                        'id': inj.id,
                        'name': name,
                        'desc': desc,
                        'value': repr(inj.calculated_value),
                        'url': f"{reverse('injectables')}{name}",
                        'valid': True
                    })
                except ObjectDoesNotExist:
                    injectables.append({
                        'id': -1,
                        'name': name,
                        'desc': 'Parameter not found',
                        'value': '',
                        'url': f"{reverse('injectables')}{name}",
                        'valid': False
                    })
                    step.valid = False
            if not step.valid:
                step.docstring = (
                    'One or more parameters are not valid. Your project seems '
                    'not to be up to date with the module. Please synchronize the '
                    'parameters (Parameters page). If the problem persists '
                    'remove this step.')
            step.injectables = injectables
        kwargs = super().get_context_data(**kwargs)
        kwargs['steps_available'] = steps_grouped if scenario else []
        kwargs['steps_scenario'] = steps_scenario
        logs = LogEntry.objects.filter(scenario=scenario).order_by('-timestamp')
        kwargs['logs'] = logs
        kwargs['show_status'] = True
        kwargs['left_columns'] = 3
        kwargs['right_columns'] = 2
        # ToDo: get room from handler

        prefix = 'ws' if settings.DEBUG else 'wss'
        kwargs['log_socket'] = \
            f'{prefix}://{self.request.get_host()}/ws/log/{scenario.id}/'
        return kwargs

    def post(self, request, *args, **kwargs):
        scenario = self.get_scenario()
        if request.POST.get('add'):
            steps = request.POST.get('steps', '').split(',')
            existing = Step.objects.filter(scenario=scenario)
            i = 0 if len(existing) == 0 else \
                existing.aggregate(Max('order'))['order__max'] + 1
            for step in steps:
                if not step:
                    continue
                Step.objects.create(scenario=scenario,
                                    name=step, order=i)
                i += 1
        elif request.POST.get('remove'):
            step_id = request.POST.get('remove')
            step = Step.objects.get(id=step_id)
            step.delete()
        elif request.POST.get('abort'):
            self.abort(request)
        elif request.POST.get('change-order'):
            data = request.POST.get('data')
            if data:
                items = json.loads(data)
                for item in items:
                    step = Step.objects.get(id=item['id'])
                    step.order = item['order']
                    step.save()
        return HttpResponseRedirect(request.path_info)

    @staticmethod
    def detail(request, *args, **kwargs):
        step_id = kwargs.get('id')
        if request.method == 'PATCH':
            try:
                step = Step.objects.get(id=step_id)
                body = json.loads(request.body)
                is_active = body.get('is_active')
                step.active = is_active
                step.save()
            except ObjectDoesNotExist:
                pass
        return HttpResponse(status=200)

    @classmethod
    def run(cls, request):
        scenario_id = request.session.get('scenario')
        if not scenario_id:
            return
        scenario_id = int(scenario_id)
        orca = manager.get(scenario_id, create=False)
        if not orca:
            return HttpResponse(status=400)
        scenario = Scenario.objects.get(id=scenario_id)

        active_steps = Step.objects.filter(
            scenario=scenario, active=True).order_by('order')
        if len(active_steps) == 0:
            orca.logger.error('No steps selected.')
            return HttpResponse(status=400)
        # check if all injectables are available
        injectables_available = orca.list_injectables()
        steps_available = orca.list_steps()
        for step in active_steps:
            if step.name not in steps_available:
                orca.logger.error(
                    'There are steps selected that can not be found in the '
                    'module. Your project seems not to be up to date '
                    'with the module. Please remove those steps.')
                return HttpResponse(status=400)
            func = orca.get_step(step.name)
            sig = signature(func._func)
            inj_parameters = sig.parameters
            required = list(set(inj_parameters) & set(injectables_available))
            inj_db = Injectable.objects.filter(name__in=required,
                                               scenario=scenario)
            if len(required) > len(inj_db):
                orca.logger.error(
                    'There are steps selected that contain injectables that '
                    'not be found. Your project seems not to be up to date '
                    'with the module.<br>Please synchronize the parameters '
                    '(parameters page).')
                return HttpResponse(status=400)
        for step in active_steps:
            step.started = None
            step.finished = None
            step.success = False
            step.save()
        apply_injectables(orca, scenario)
        if manager.is_running(scenario.id):
            orca.logger.error('Orca is already running. Please wait for it to '
                         'finish or abort it.')
            return HttpResponse(status=400)

        message = f'Running Steps for scenario "{scenario.name}"'
        orca.logger.info(message)

        run, created = Run.objects.get_or_create(scenario=scenario)
        run.run_by = request.user
        run.success = False
        run.started = timezone.now()
        run.finished =  None
        run.save()

        def on_success():
            run.success = True
            run.finished = timezone.now()
            run.save()
        def on_error():
            run.success = False
            run.finished = timezone.now()
            run.save()

        try:
            manager.start(scenario.id, steps=active_steps,
                          on_success=on_success, on_error=on_error)
        # ToDo: specific exceptions
        except Exception as e:
            orca.logger.error(str(e))
            return HttpResponse(status=400)
        return HttpResponse(status=200)

    @staticmethod
    def abort(request, *args, **kwargs):
        scenario_id = int(kwargs.get('id'))
        manager = OrcaManager()
        manager.abort(scenario_id)
        return HttpResponse(status=200)


class StepsListView(ProjectMixin, ListView):

    def get(self, request):
        if request.method == 'POST':
            body = json.loads(request.body)
            for item in body:
                step = Step.objects.get(id=item['id'])
                step.order = item['order']
                step.save()
        scenario_id = request.session.get('scenario')
        if scenario_id is None:
            return HttpResponseNotFound('scenario not found')
        scenario = self.get_scenario()
        orca = self.get_orca()
        steps_scenario = Step.objects.filter(
            scenario=scenario).order_by('order')
        steps_json = []
        steps_available = orca.list_steps()
        for step in steps_scenario:
            if step.name not in steps_available:
                continue
            func = orca.get_step(step.name)
            started = step.started
            finished = step.finished
            lz = tz.tzlocal()
            if started:
                started = started.astimezone(lz).strftime('%d.%m.%Y %H:%M:%S')
            if finished:
                finished = finished.astimezone(lz).strftime('%d.%m.%Y %H:%M:%S')
            steps_json.append({
                'id': step.id,
                'name': step.name,
                'started': started,
                'finished': finished,
                'success': step.success,
                'order': step.order,
                'is_active': step.active,
                'module': func._func.__module__,
            })
        return JsonResponse(steps_json, safe=False)


class LogsView(ProjectMixin, ListView):
    template_name = 'orcaserver/logs.html'
    model = LogEntry
    context_object_name = 'logs'

    def get_queryset(self):
        """Return the injectables with their values."""
        scenario_id = self.kwargs.get('id')
        logs = LogEntry.objects.filter(scenario_id=scenario_id)
        lz = tz.tzlocal()
        for log in logs:
            log.filtered_timestamp = log.timestamp.astimezone(lz).strftime(
                '%d.%m.%Y %H:%M:%S.%f')
        return logs

    def post(self, request, *args, **kwargs):
        scenario_id = self.kwargs.get('id')
        if request.POST.get('clear'):
            logs = LogEntry.objects.filter(scenario_id=scenario_id)
            logs.delete()
        return HttpResponse(status=200)