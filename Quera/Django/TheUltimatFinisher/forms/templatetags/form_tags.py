from django import template
from django.utils.safestring import mark_safe

import markdown
import re

register = template.Library()


@register.filter
def render_markdown(text):
    return ''


@register.filter
def extract_field_id(field_name):
    return ''


@register.filter
def get_field_type_icon(field_type):
    return ''


@register.filter
def percentage(value, total):
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0


@register.filter
def add_class(field, css_class):
    
    if hasattr(field, 'field'):
        widget = field.field.widget
        if hasattr(widget, 'attrs'):
            existing_class = widget.attrs.get('class', '')
            if existing_class:
                widget.attrs['class'] = f"{existing_class} {css_class}"
            else:
                widget.attrs['class'] = css_class
        return field
    return field
