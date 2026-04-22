from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dictionary lookup using a variable key"""
    if dictionary:
        # Convert key to string if necessary, or keep as int/str based on your dict keys
        return dictionary.get(key) or dictionary.get(str(key))
    return None