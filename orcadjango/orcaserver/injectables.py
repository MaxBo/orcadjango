
from django import forms
from django.contrib.gis.geos import MultiPolygon, fromstr
import json
import ast
import ogr
import datetime
from django.core.validators import RegexValidator
import importlib
import ast
from django.db import models
from django.core.validators import int_list_validator
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from orcaserver.management import OrcaManager, parse_injectables
from orcaserver.widgets import (EditableDictWidget, CommaSeparatedCharField,
                                OgrGeometryField, OsmMultiPolyWidget, DictField)
from orcaserver.models import Scenario, NameModel


class Injectable(NameModel):
    name = models.TextField()
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)
    value = models.TextField(null=True)
    datatype = models.TextField(null=True, blank=True)
    data_class = models.TextField(null=True, blank=True)
    parent_injectables = models.TextField(
        validators=[int_list_validator], default='[]')

    def __str__(self):
        return f'{self.scenario} - {self.name}'

    @property
    def can_be_changed(self):
        if self.parent_injectable_values:
            return False
        conv = OrcaTypeMap.get(self.data_class)
        # only data types with an implemented converter should be changable
        # via UI, the default converter has no datatype
        if not conv.data_type:
            return False
        return True

    @property
    def meta(self):
        orca = OrcaManager().get(self.scenario.id,
                                 module=self.scenario.project.module)
        return parse_injectables(orca, injectables=[self.name])[self.name]

    @property
    def calculated_value(self):
        """The calculated value"""
        if self.can_be_changed:
            return self.value
        orca = OrcaManager().get(self.scenario.id,
                                 module=self.scenario.project.module)
        return orca.get_injectable(self.name)

    @property
    def repr_html(self) -> str:
        """HTML-representation of the value according to the type"""
        try:
            if self.datatype == 'DataFrame':
                ret = self.calculated_value.to_html()
            if self.datatype in ['DataArray', 'Dataset']:
                ret = self.calculated_value._repr_html_()
            ret = str(self.calculated_value)
        except Exception as e:
            ret = repr(e)
        return ret

    @property
    def validated_value(self):
        # ToDo: some validation
        value = self.value
        if self.can_be_changed:
            conv = OrcaTypeMap.get(self.data_class)
            value = conv.to_value(value)
        return value

    @property
    def parent_injectable_values(self):
        parent_injectables = ast.literal_eval(self.parent_injectables)
        injectables = Injectable.objects.filter(id__in=parent_injectables)
        inj_names = injectables.values_list('name', flat=True)
        return ','.join(inj_names)

    @property
    def parent_injectable_urls(self):
        reverse_url = reverse('injectables')
        return {name: f'{reverse_url}{name}'
                for name in self.parent_injectable_values.split(',')}

    def save(self, **kwargs):
        if self.value is not None and not isinstance(self.value, str):
            conv = OrcaTypeMap.get(self.data_class)
            self.value = conv.to_str(self.value)
        super().save(**kwargs)

    def get_form_field(self):
        converter = OrcaTypeMap.get(self.data_class)
        meta = self.meta
        if not meta:
            return
        if 'choices' in meta:
            choices = meta['choices'].split(',')
            choices = tuple(zip(choices, choices))
            field = converter.get_choice_field(
                value=self.validated_value, choices=choices)
        else:
            field = converter.get_form_field(
                value=self.validated_value, label=f'Value',
                placeholder=meta['docstring'],
                injectable_name=self.name, meta=meta,
                project=self.scenario.project)
        return field


@deconstructible
class UniqueInjValidator:
    message = _('Value is already in use in another project.')
    code = 'invalid'
    project = None
    injectable_name = None

    def __init__(self, injectable_name: str, project: 'Project'=None):
        self.injectable_name = injectable_name
        self.project = project

    def __call__(self, value):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """
        injectables = Injectable.objects.filter(name=self.injectable_name,
                                                value=value)
        if self.project:
            injectables = injectables.exclude(scenario__project=self.project)
        if len(injectables) > 0:
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return (
            isinstance(other, UniqueValidator) and
            self.project == other.project and
            self.injectable_name == other.injectable_name
        )


class OrcaTypeMap:
    data_type = None
    form_field = None
    description = ''

    @staticmethod
    def get(module):
        cls = None
        try:
            if isinstance(module, str):
                module_class = module.split('.')
                module_name = '.'.join(module_class[:-1])
                classname = module_class[-1]
                module = getattr(importlib.import_module(module_name),
                                 classname, str)
            for sub in OrcaTypeMap.__subclasses__():
                if sub.data_type == module:
                    cls = sub
                    break
        except ModuleNotFoundError:
            pass
        if not cls:
            cls = DefaultConverter
        return cls()

    def to_value(self, text):
        raise NotImplementedError

    def to_str(self, value):
        return str(value)

    def get_form_field(self, value=None, label='', placeholder='value',
                       pattern=None, pattern_help=None, project=None,
                       injectable_name=None, meta=None):
        validators = []
        if meta and meta.get('regex'):
            regex = meta.get('regex')
            validators.append(
                RegexValidator(regex, meta.get('regex_help', regex)))
        if injectable_name and meta and meta.get('unique'):
            validators.append(
                UniqueInjValidator(injectable_name, project=project))
        field = self.form_field(initial=value, label=label,
                                validators=validators)
        field.widget.attrs['placeholder'] = placeholder
        return field

    def get_choice_field(self, value=None, choices=(), label='Please select:'):
        return forms.ChoiceField(choices=choices, label=label, initial=value)


class DefaultConverter(OrcaTypeMap):
    form_field = forms.CharField

    def to_value(self, text):
        return ast.literal_eval(text)


class IntegerConverter(OrcaTypeMap):
    data_type = int
    form_field = forms.IntegerField
    description = 'integer'

    def to_value(self, text):
        return int(text)


class FloatConverter(OrcaTypeMap):
    data_type = float
    form_field = forms.FloatField
    description = 'float'

    def to_value(self, text):
        return float(text)


class BooleanConverter(OrcaTypeMap):
    data_type = bool
    form_field = forms.BooleanField
    description = 'boolean'

    def get_form_field(self, value, label='', **kwargs):
        return self.form_field(initial=value, label='True', required=False)

    def to_value(self, text):
        return text.lower() == 'true'


class ListConverter(OrcaTypeMap):
    data_type = list
    form_field = CommaSeparatedCharField
    description = 'comma seperated values'

    def to_str(self, value):
        return ', '.join(str(v) for v in value)

    def to_value(self, text):
        return [t.strip() for t in text.split(',')] if text else []

    def get_choice_field(self, value=None, choices=(),
                         label='Select one or more'):
        return forms.MultipleChoiceField(choices=choices, label=label,
                                         widget=forms.CheckboxSelectMultiple,
                                         initial=value)


class DictConverter(OrcaTypeMap):
    data_type = dict
    form_field = forms.CharField
    description = 'dictionary'

    def get_form_field(self, value, label='', meta=None,
                       **kwargs):
        if meta and not meta.get('editable_keys'):
            return DictField(value, label=label)
        return forms.CharField(initial=value, label=label,
                               widget=EditableDictWidget)

    def to_str(self, value):
        return json.dumps(value)

    def to_value(self, text):
        # workaround
        # ToDo: remove this
        try:
            ret = json.loads(text)
        except json.decoder.JSONDecodeError:
            ret = json.loads(text.replace("'",'"'))
        return ret


class StringConverter(OrcaTypeMap):
    data_type = str
    form_field = forms.CharField
    description = 'string'

    def to_value(self, text):
        return text


class GeometryConverter(OrcaTypeMap):
    data_type = ogr.Geometry
    form_field = OgrGeometryField
    srid = 4326

    def to_str(self, value):
        if not value:
            #return 'POLYGON EMPTY'
            return
        # ToDo: this is inplace, might cause side effects
        value.FlattenTo2D()
        return value.ExportToWkt()

    def to_value(self, text):
        if not text:
            return
        geom = ogr.CreateGeometryFromWkt(text)
        geom.FlattenTo2D()
        s_ref = ogr.osr.SpatialReference()
        s_ref.ImportFromEPSG(self.srid)
        geom.AssignSpatialReference(s_ref)
        return geom

    def get_form_field(self, value, label='', **kwargs):
        if value:
            poly = fromstr(self.to_str(value))
            if not isinstance(poly, MultiPolygon):
                poly = MultiPolygon(poly)
            poly.srid = self.srid
        else:
            poly = None
        return self.form_field(
            srid=self.srid,
            geom_type='MultiPolygon',
            initial=poly,
            label=label,
            widget= OsmMultiPolyWidget(
                attrs={
                    'map_width': 800,
                    'map_height': 500,
                    'display_wkt': True,
                    'placeholder': ('WKT string (preferably in 3857 to be able '
                                    'to render it on map)'),
                    #'default_zoom': 5
                }
            )
        )

    def get_choice_field(self, *args, **kwargs):
        raise NotImplementedError


class DateConverter(OrcaTypeMap):
    data_type = datetime.date
    date_format = '%d.%m.%Y'
    form_field = forms.DateField

    def to_str(self, value):
        if not value:
            return ''
        return value.strftime(self.date_format)

    def to_value(self, text):
        if not text:
            return
        try:
            dt = datetime.datetime.strptime(text, self.date_format).date()
        except ValueError:
            return
        return dt

    def get_choice_field(self, *args, **kwargs):
        raise NotImplementedError

    def get_form_field(self, value=None, label='Pick a date', **kwargs):
        field = self.form_field(input_formats=[self.date_format],
                                label=label, initial=value,
                                widget=forms.DateInput(format=self.date_format))
        return field


