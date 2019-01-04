from django import forms
from .models import Scenario

def get_scenarios():
    """get the id and the name of all scenarios"""
    scenarios = ((c.id, c.name) for c in Scenario.objects.all())
    return scenarios


class ScenarioForm(forms.Form):
    scenario = forms.ChoiceField(choices=get_scenarios)


class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)


class InjectablesPopulateForm(forms.Form):
    """Populate Injectables Button"""

