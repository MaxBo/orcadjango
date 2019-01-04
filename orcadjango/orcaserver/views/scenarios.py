from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin, BaseFormView
from orcaserver.models import Scenarios, ScenarioList
from orcaserver.forms import ScenarioForm


class ScenariosView(BaseFormView, ListView):
    model = Scenarios
    form_class = ScenarioForm
    success_url = '/orca/scenarios'
