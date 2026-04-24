"""Compatibility template tags for Django template partials."""

import django
from django import template


if django.VERSION < (6, 0):
    from template_partials.templatetags.partials import register
else:
    register = template.Library()
