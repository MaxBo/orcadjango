from django.views.generic import FormView

from orcaserver.forms import OrcaFileForm
from orcaserver.views import ProjectMixin
from orcaserver.management import OrcaManager


class SettingsView(ProjectMixin, FormView):
    template_name = 'orcaserver/settings.html'
    form_class = OrcaFileForm
    success_url = '/projects'

    def form_valid(self, form):
        module = form.cleaned_data['module']
        OrcaManager().set_module(module)
        return super().form_valid(form)
