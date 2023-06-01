from django import forms
from django.contrib.gis.geos import MultiPolygon, fromstr
import json
import ast
from osgeo import ogr
import datetime
from django.core.validators import RegexValidator
import importlib
import ast
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from orcaserver.widgets import (EditableDictWidget, CommaSeparatedCharField,
                                OgrGeometryField, OsmMultiPolyWidget, DictField)


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
        if (isinstance(value, str)):
            return value
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
