from django import forms
from django.conf import settings

from orcaserver.models import Step, InjectableConversionError
from orcaserver.management import OrcaManager


def get_python_module():
    """return the currently set python module"""
    return OrcaManager().python_module

def get_available_modules():
    available = settings.ORCA_MODULES.get('available', {})
    return [(v.get('path'),
             k + f" - {v['description']} " if 'description' in v else '')
            for k, v in available.items()]


class OrcaSettingsForm(forms.Form):
    choices = forms.ChoiceField(
        widget=forms.Select(
        attrs={'onchange': "document.querySelector('input[name=\"module\"]').value=this.value;"}),
        choices=get_available_modules(),
        label='Available modules',
        initial=get_python_module,
    )
    module = forms.CharField(
        max_length=100,
        widget=forms.widgets.TextInput(
            attrs={'size': 100, }),
        label='Python module with orca imports',
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
