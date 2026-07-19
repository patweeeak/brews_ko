from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return ''


@register.filter
def peso(value):
    """Format a number as Philippine peso currency, e.g. 150 -> ₱150.00"""
    try:
        return f"₱{float(value):,.2f}"
    except (TypeError, ValueError):
        return value
