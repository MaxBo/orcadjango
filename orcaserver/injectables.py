import json
import ast
import pandas
from osgeo import ogr
import datetime
import importlib
import ast
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class OrcaTypeMap:
    data_type = None
    description = ''

    @staticmethod
    def get(mod_str):
        cls = None
        module = None
        if isinstance(mod_str, str):
            try:
                module_class = mod_str.split('.')
                module_name = '.'.join(module_class[:-1])
                classname = module_class[-1]
                module = getattr(importlib.import_module(module_name),
                                 classname, str)
            except ModuleNotFoundError:
                pass
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

    def to_value(self, text):
        return ast.literal_eval(text)


class IntegerConverter(OrcaTypeMap):
    data_type = int
    description = 'integer'

    def to_value(self, text):
        return int(text)


class FloatConverter(OrcaTypeMap):
    data_type = float
    description = 'float'

    def to_value(self, text):
        return float(text)


class BooleanConverter(OrcaTypeMap):
    data_type = bool
    description = 'boolean'

    def to_value(self, text):
        return text.lower() == 'true'


class ListConverter(OrcaTypeMap):
    data_type = list
    description = 'comma seperated values'

    def to_str(self, value):
        return ', '.join(str(v) for v in value)

    def to_value(self, text):
        return [t.strip() for t in text.split(',')] if text else []


class DictConverter(OrcaTypeMap):
    data_type = dict
    description = 'dictionary'

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
    description = 'string'

    def to_value(self, text):
        return text


class GeometryConverter(OrcaTypeMap):
    data_type = ogr.Geometry
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