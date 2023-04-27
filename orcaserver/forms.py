from django import forms
from django.contrib.gis import forms as geoforms
from django.conf import settings
import time
import json

from orcaserver.models import Step
from orcaserver.management import OrcaManager
from orcaserver.injectables import OrcaTypeMap

def get_python_module():
    """return the currently set python module"""
    return OrcaManager().default_module

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
        label='Module path',
        initial=get_python_module,
    )


class InjectableValueForm(geoforms.Form):

    def __init__(self, *args, **kwargs):
        inj = kwargs.pop('injectable', None)
        super().__init__(*args, **kwargs)
        if inj.can_be_changed:
            field = inj.get_form_field()
            if field:
                self.fields['value'] = field

    def clean(self):
        return super().clean()


class ProjectForm(forms.Form):
    name = forms.CharField(label='Project name', max_length=255)
    description = forms.CharField(label='Description')

    def __init__(self, *args, **kwargs):
        active_mod = kwargs.pop('module')
        project = kwargs.pop('project', None)
        project_name = project.name if project else ''
        project_description = project.description if project else ''
        initial_values = json.loads(project.init) if project else {}
        super().__init__(*args, **kwargs)
        self.fields['name'].initial = project_name
        self.fields['description'].initial = project_description
        available_mods = settings.ORCA_MODULES.get('available')

        mod_descs = list(filter(lambda mod: mod['path'] == active_mod,
                                available_mods.values()))
        if len(mod_descs) > 1:
            raise Exception('more than one module defined with same path in '
                            'settings')
        if len(mod_descs) == 0:
            return kwargs

        module_name = mod_descs[0]['path']
        initial = mod_descs[0].get('init', [])
        manager = OrcaManager()
        uid = str(time.time())
        orca = manager.get(uid, module=module_name)
        meta = parse_injectables(orca)
        for injectable in initial:
            desc = meta[injectable]
            converter = OrcaTypeMap.get(desc['data_class'])
            value = initial_values.get(injectable)
            if value:
                value = converter.to_value(value)
            else:
                value = desc['value']
            label = f'Initial value for "{injectable}" - {desc["docstring"]}'
            field = converter.get_form_field(value=value, label=label,
                                             project=project, meta=desc,
                                             injectable_name=injectable)
            self.fields[injectable] = field
        manager.remove(uid)


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