from django.views.generic import ListView
from django.views.generic.edit import FormView, FormMixin, BaseFormView
from django_sorting_field.fields import sort_by_order
from orcaserver.models import Scenarios, ScenarioList
from orcaserver.forms import ScenarioForm


class ScenariosView(BaseFormView, ListView):
    model = Scenarios
    form_class = ScenarioForm
    success_url = '/orca/scenarios'


    def render_to_response(self, context, **response_kwargs):
        context.update({
            "id_order_list": sort_by_order(
                    self.model.objects.all(),
                    self.model.objects.values_list('order')
            ),
        })
        return super().render_to_response(context, **response_kwargs)
