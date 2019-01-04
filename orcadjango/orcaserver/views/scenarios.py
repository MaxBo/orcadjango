from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin, BaseFormView
from orcaserver.models import Scenario
from orcaserver.forms import ScenarioForm


class ScenariosView(BaseFormView, ListView):
    model = Scenario
    form_class = ScenarioForm
    success_url = '/orca/scenarios'
    template_name = 'orcaserver/scenario_list.html'

    def form_valid(self, form):
        """set the selected scenario as session attribute"""
        action = self.request.POST.get('action')
        if action == 'Select Scenario':
            scenario_id = form.cleaned_data.get('scenario')
            self.request.session['scenario'] = scenario_id
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        """get the selected scenario from the session attribute"""
        scenario_id = request.session.get('scenario')
        self.initial['scenario'] = scenario_id
        return super().get(request, *args, **kwargs)
