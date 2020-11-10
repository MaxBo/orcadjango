from django.views.generic import FormView
import importlib

from orcaserver.forms import OrcaSettingsForm
from orcaserver.views import ProjectMixin


class SettingsView(ProjectMixin, FormView):
    template_name = 'orcaserver/settings.html'
    form_class = OrcaSettingsForm
    success_url = '/projects'

    def form_valid(self, form):
        module = form.cleaned_data['module']
        if not importlib.util.find_spec(module):
            form.add_error('module', 'Module not found')
            return super().form_invalid(form)
        self.request.session['module'] = module
        return super().form_valid(form)
