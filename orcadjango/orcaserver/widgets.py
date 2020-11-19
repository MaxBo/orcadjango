from django import forms
from django.core import validators
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.contrib.gis.geos import GEOSException
from django.contrib.gis import forms as geoforms
from osgeo.gdal import ogr


class CommaSeparatedCharField(forms.Field):
    def __init__(self, *args, **kwargs):
        if 'initial' in kwargs:
            kwargs['initial'] = ', '.join(kwargs['initial'])
        super().__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)

    def to_python(self, value):
        value = [v.strip() for v in value.split(',') if v.strip()]
        return value


class DictField(forms.MultiValueField):

    def __init__(self, dictionary, *args, **kwargs):
        self.dictionary = dictionary
        fields = []
        for k, v in dictionary.items():
            fields.append(forms.CharField(widget=forms.TextInput(),
                                          label=k, initial=v))
        widget = DictWidget(list(dictionary.keys()), fields,
                                 {'style': 'margin-left: 10px;'})
        super().__init__(fields, widget=widget, *args, **kwargs)

    def compress(self, data):
        if not data:
            return
        if isinstance(data, dict):
            return data
        else:
            return dict(zip(self.dictionary.keys(), data))

    def clean(self, value):
        clean_data = []
        errors = ErrorList()
        for field in self.fields:
            key = field.label
            v = value.get(key)
            if field.required and v in validators.EMPTY_VALUES:
                errors.append(f"{key}: {self.error_messages['required']}")
            try:
                clean_data.append(field.clean(v))
            except ValidationError as e:
                errors.extend(f"{key}: {message}" for message in e.messages)
        if errors:
            raise ValidationError(errors)
        ret = self.compress(clean_data)
        self.validate(ret)
        return ret


class GeometryField(geoforms.GeometryField):
    def clean(self, value):
        geom = forms.Field.clean(self, value)
        if geom is None:
            return

        # there is a bug in the super class, you can not pass the geometry type
        # to OL with all upper but starting with capital letter
        if (str(geom.geom_type).upper() != self.geom_type.upper() and
            not self.geom_type.upper() == 'GEOMETRY'):
            raise forms.ValidationError(
                self.error_messages['invalid_geom_type'],
                code='invalid_geom_type')

        if self.srid and self.srid != -1 and self.srid != geom.srid:
            try:
                geom.transform(self.srid)
            except GEOSException:
                raise forms.ValidationError(
                    self.error_messages['transform_error'],
                    code='transform_error')

        return ogr.CreateGeometryFromWkt(geom.wkt)


class DictWidget(forms.widgets.MultiWidget):

    def __init__(self, keys, fields, attrs=None):
        self.keys = keys
        self.fields = fields
        super().__init__([f.widget for f in fields], attrs)

    def render(self, name, value, attrs={}, renderer=None):
        if not isinstance(value, list):
            value = self.decompress(value)

        attrs = self.build_attrs(attrs)
        _id = attrs.pop('id')
        required = attrs.pop('required')
        attrs['name'] = _id
        _attrs = ' '.join([f'{k}="{v}"' for k,v in attrs.items()])
        html = [f'<table {_attrs}>']

        for idx, field in enumerate(self.fields):
            html.append('<tr>')
            key = self.keys[idx]
            widget = field.widget
            widget_id = f'{_id}_{key}'
            widget_attrs = {
                'style': 'margin-left: 5px',
                'id': widget_id,
                'required': True
            };
            html.append(f'<td><label for {widget_id}>{field.label}</label></td>')
            widget_html = widget.render(f'{name}_{key}',
                                        field.initial,
                                        widget_attrs,
                                        renderer=renderer)
            html.append(f'<td>{widget_html}</td>')
            html.append('</tr>')
        html.append('</table>')
        return mark_safe(''.join(html))

    def id_for_label(self, _id):
        return _id

    def value_from_datadict(self, data, files, name):
        ret = {}
        for key in self.keys:
            ret[key] = data.get(f'{name}_{key}')
        return ret

    def decompress(self, value):
        if value not in validators.EMPTY_VALUES:
            return [value.get(k, None) for k in self.keys]
        else:
            return [None] * len(self.keys)