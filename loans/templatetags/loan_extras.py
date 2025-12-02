from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
