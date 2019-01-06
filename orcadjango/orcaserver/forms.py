import os
import orca
from django import forms
from .models import Scenario


class OrcaFileForm(forms.Form):
    module = forms.CharField(max_length=100,
                             widget=forms.widgets.TextInput(
                                 attrs={'size': 100,}),
                             label='python module with orca imports',
                             initial='orcaserver.tests.dummy_orca_stuff',
                             )


def get_orca_steps():
    """get a list of all orca steps available"""
    return [(step, step) for step in orca.list_steps()]


class StepsForm(forms.Form):
    steps = forms.MultipleChoiceField(required=False,
                                      widget=forms.CheckboxSelectMultiple,
                                      choices=get_orca_steps)


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


class StepsPopulateForm(forms.Form):
    """Populate Injectables Button"""

