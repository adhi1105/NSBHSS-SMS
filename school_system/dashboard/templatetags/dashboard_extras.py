from django import template

register = template.Library()

@register.filter(name='replace_chars')
def replace_chars(value, arg):
    """
    Usage: {{ value|replace_chars:"_, " }}
    """
    if not value:
        return ""
    try:
        # Splits the argument "_, " into old="_" and new=" "
        old, new = arg.split(',')
        return str(value).replace(old, new)
    except:
        return value