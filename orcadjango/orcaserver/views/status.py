from django.views.generic import ListView
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseNotFound

from orcaserver.views import ProjectMixin
from orcaserver.models import Scenario
from orcaserver.management import OrcaManager


class StatusView(ProjectMixin, ListView):
    template_name = 'orcaserver/status.html'
    model = Scenario
    context_object_name = 'scenarios'

    def get_queryset(self):
        """Return the injectables with their values."""
        scenarios = Scenario.objects.filter(project__module=self.get_module())
        return scenarios

    def list(self):
        pass

    @staticmethod
    def detail(request, *args, **kwargs):
        scenario_id = kwargs.get('id')
        manager = OrcaManager()
        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound('scenario not found')
        project = scenario.project
        other_running = []
        for scn in project.scenario_set.all():
            if scn.id != scenario_id and manager.is_running(scn.id):
                other_running.append(scenario)
        is_running = manager.is_running(scenario_id)
        meta = manager.get_meta(scenario_id)
        user = meta.get('user')
        user_name = user.get_username() if user else 'unknown'
        start_time = meta.get('start_time', '-')
        status_text = (
            'project not in use'
            if not is_running and len(other_running) == 0
            else ('project is in use')
        )
        status_text += '<br>'
        status_text += (
            f'scenario "{scenario.name}" is currently run by user "{user}"'
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