from django.views.generic import FormView
import importlib

from orcaserver.forms import OrcaFileForm
from orcaserver.views import ProjectMixin
from orcaserver.management import OrcaManager


class SettingsView(ProjectMixin, FormView):
    template_name = 'orcaserver/settings.html'
    form_class = OrcaFileForm
    success_url = '/projects'

    def form_valid(self, form):
        module = form.cleaned_data['module']
        if not importlib.util.find_spec(module):
            form.add_error('module', 'Module not found')
            return super().form_invalid(form)
        OrcaManager().set_module(module)
        return super().form_valid(form)
