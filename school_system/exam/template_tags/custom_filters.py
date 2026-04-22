from django import template

# This variable MUST be named 'register'
register = template.Library()

@register.filter
def get_mark(dictionary, key):
    # ... your logic ...
    if not dictionary: return ''
    data = dictionary.get(str(key)) or dictionary.get(key)
    return data['mark'] if data else ''

@register.filter
def get_remark(dictionary, key):
    # ... your logic ...
    if not dictionary: return ''
    data = dictionary.get(str(key)) or dictionary.get(key)
    return data['remark'] if data else ''