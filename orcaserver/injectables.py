from django import forms
from django.contrib.gis.geos import MultiPolygon, fromstr
import json
import ast
import pandas
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
    def get(mod_str):
        cls = None
        if isinstance(mod_str, str):
            try:
                module_class = mod_str.split('.')
                module_name = '.'.join(module_class[:-1])
                classname = module_class[-1]
                module = getattr(importlib.import_module(module_name),
                                 classname, str)
            except ModuleNotFoundError:
                module = None
        for sub in OrcaTypeMap.__subclasses__():
            comp = mod_str if isinstance(sub.data_type, str) else module
            if sub.data_type == comp:
                cls = sub
                break
        if not cls:
            cls = DefaultConverter
        return cls()

    def to_value(self, text):
        raise NotImplementedError

    def to_str(self, value):
        return str(value)


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


class DateConverter(OrcaTypeMap):
    data_type = datetime.date
    date_format = '%Y-%m-%d'
    form_field = forms.DateField

    #def to_str(self, value):
        #if not value:
            #return ''
        #return value.strftime(self.date_format)

    def to_value(self, text):
        if not text:
            return
        try:
            dt = datetime.datetime.strptime(text, self.date_format).date()
        except ValueError:
            return
        return dt


class DataframeConverter(OrcaTypeMap):
    data_type = pandas.core.frame.DataFrame

    def to_str(self, value):
        if value is None:
            return ''
        return value.to_json()

    def to_value(self, text):
        if not text:
            return
        return pandas.read_json(text)


class XArrayDatasetConverter(OrcaTypeMap):
    data_type = 'xarray.core.dataset.Dataset'

    def to_str(self, value):
        if value is None:
            return ''
        return value.to_pandas().to_json()

    def to_value(self, text):
        if not text:
            return
        return pandas.read_json(text).to_xarray()