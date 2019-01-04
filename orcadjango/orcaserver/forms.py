from django import forms
from .models import Scenarios, ScenarioList


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenarios
        fields = ['name', 'order']


class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)


class InjectablesPopulateForm(forms.Form):
    """Populate Injectables Button"""

