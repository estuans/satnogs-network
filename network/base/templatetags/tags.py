from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.simple_tag
def active(request, urls):
    if request.path in (reverse(url) for url in urls.split()):
        return 'active'
    return None


@register.filter
def frq(value):
    try:
        to_format = float(value)
    except (TypeError, ValueError):
        return '-'
    formatted = format(float(to_format) / 1000000, '.3f')
    formatted = formatted + ' MHz'
    return formatted


@register.filter
def percentagerest(value):
    try:
        return 100 - value
    except (TypeError, ValueError):
        return 0


@register.filter
def truncatesecs(value):
    try:
        return value[:-3]
    except (TypeError, ValueError):
        return value
