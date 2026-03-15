from django import template
from django.contrib.auth.models import Group 

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if a user belongs to a specific security group.
    Usage: {% if request.user|has_group:"Teacher" %}
    """
    try:
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False