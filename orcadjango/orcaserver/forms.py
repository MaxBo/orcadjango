from django import forms
from django_sorting_field.fields import SortingFormField
from .models import Scenarios, ScenarioList


class ScenarioForm(forms.ModelForm):
    order = SortingFormField()
    class Meta:
        model = Scenarios
        fields = ['name', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["order"].populate(
                items=self.instance.name.all(),
            )
        self.fields['order'].populate(self.Meta.model.objects.all())

class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)


class InjectablesPopulateForm(forms.Form):
    """Populate Injectables Button"""

