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


class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)


