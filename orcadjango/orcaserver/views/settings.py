from django.views.generic import FormView

from orcaserver.forms import OrcaFileForm
from orcaserver.management.commands import runorca


class SettingsView(FormView):
    template_name = 'orcaserver/settings.html'
    form_class = OrcaFileForm
    success_url = '/scenarios'

    def form_valid(self, form):
        module = form.cleaned_data['module']
        runorca.load_module(module)
        return super().form_valid(form)
