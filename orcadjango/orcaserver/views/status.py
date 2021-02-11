from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseNotFound

from orcaserver.models import Scenario, Run
from orcaserver.management import OrcaManager
from dateutil import tz

TIME_FORMAT = '%d.%m.%Y %H:%M:%S'


class StatusView(TemplateView):
    template_name = 'orcaserver/status.html'
    #model = Run
    #context_object_name = 'runs'

    #def get_queryset(self):
        #"""Return the injectables with their values."""
        #runs = Run.objects.all()#filter(scenario__project__module=self.get_module())
        #return runs

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['left_columns'] = 0
        kwargs['center_columns'] = 12
        kwargs['right_columns'] = 0
        return kwargs

    @staticmethod
    def list(request):
        manager = OrcaManager()
        runs = Run.objects.all()
        runs_json = []
        for run in runs:
            started = run.started
            finished = run.finished
            user = run.run_by
            lz = tz.tzlocal()
            if started:
                started = started.astimezone(lz).strftime(TIME_FORMAT)
            if finished:
                finished = finished.astimezone(lz).strftime(TIME_FORMAT)
            scenario = run.scenario
            project = scenario.project
            runs_json.append({
                'module': project.module,
                'project_name': project.name,
                'scenario_name': scenario.name,
                'scenario_id': scenario.id,
                'started': started,
                'finished': finished,
                'run_by': user.get_username() if user else '',
                'is_running': manager.is_running(run.scenario.id),
                'success': run.success,
            })
        return JsonResponse({'runs': runs_json}, safe=False)

    @staticmethod
    def detail(request, *args, **kwargs):
        scenario_id = kwargs.get('id')
        manager = OrcaManager()
        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound('scenario not found')
        scenario_id = int(scenario_id)
        project = scenario.project
        other_running = []
        for scn in project.scenario_set.all():
            if scn.id != scenario_id and manager.is_running(scn.id):
                other_running.append(scenario)
        is_running = manager.is_running(scenario_id)
        run, created = Run.objects.get_or_create(scenario=scenario)
        user_name = run.run_by.get_username() if run.run_by else 'unknown'
        start_time = run.started
        lz = tz.tzlocal()
        if start_time:
            start_time = start_time.astimezone(lz).strftime(TIME_FORMAT)
        status_text = (
            'project not in use' if not is_running and len(other_running) == 0
            else ('project is in use')
        )
        status_text += '<br>'
        status_text += (
            f'scenario "{scenario.name}" is currently run by user "{user_name}"'
            if is_running else f'scenario "{scenario.name}" not in use'
        )
        status = {
            'running': is_running,
            'other_running_in_project': [s.name for s in other_running],
            'text': status_text,
            'last_user': user_name,
            'last_start': start_time
        }
        return JsonResponse(status)