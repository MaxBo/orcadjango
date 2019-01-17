import orca
from django import forms


def get_python_module():
    """return the default python module"""
    module_name = getattr(orca,
                          '_python_module',
                          'orcaserver.tests.dummy_orca_stuff')
    return module_name


class OrcaFileForm(forms.Form):
    module = forms.CharField(max_length=100,
                             widget=forms.widgets.TextInput(
                                 attrs={'size': 100, }),
                             label='python module with orca imports',
                             initial=get_python_module,
                             )


class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)
