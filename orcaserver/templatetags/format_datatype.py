from django import template

register = template.Library()

@register.filter
def format_datatype(value):
    return value.replace('typing.', '')