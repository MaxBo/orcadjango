import orca
from django import forms
from django.conf import settings
from .models import Step
from orcaserver.models import Injectable, InjectableConversionError


def get_python_module():
    """return the default python module"""
    module_name = getattr(orca,
                          '_python_module',
                          settings.ORCA_MODULE)
    return module_name


class OrcaFileForm(forms.Form):
    module = forms.CharField(max_length=100,
                             widget=forms.widgets.TextInput(
                                 attrs={'size': 100, }),
                             label='python module with orca imports',
                             initial=get_python_module,
                             )


class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=255)

    def __init__(self, *args, **kwargs):
        self.injectable = kwargs.pop('injectable', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        value = self.cleaned_data['value']

        try:
            _ = self.injectable.validate_value(value=value)
        except InjectableConversionError as e:
            self.add_error('value', str(e))
            raise forms.ValidationError(str(e))


class StepForm(forms.ModelForm):
    class Meta:
        model = Step
        exclude = ()
        widgets={
            'is_active': forms.RadioSelect(
                attrs={
                    'class':'custom-control-input custom-control-label',
                }
            ),
        }
