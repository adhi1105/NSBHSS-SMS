# staff/decorators.py
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from functools import wraps

# --- EXISTING SPECIFIC CHECKERS ---
def is_librarian(user):
    return user.is_superuser or user.groups.filter(name='Librarian').exists()

def is_cashier(user):
    return user.is_superuser or user.groups.filter(name='Cashier').exists()

def is_office_staff(user):
    return user.groups.filter(name='Office_Staff').exists() or user.is_superuser

def is_dept_admin(user):
    return user.groups.filter(name='Dept_Admin').exists() or user.is_superuser

def is_guest(user):
    return not user.is_authenticated or user.groups.filter(name='Guest').exists()

# --- THE MISSING COMPONENT: ALLOWED USERS FACTORY ---
def allowed_users(allowed_roles=[]):
    """
    Universal decorator for Eduplex Identity Management.
    Checks if a user belongs to any of the roles provided in the list.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                # Gets the first group assigned to the user
                group = request.user.groups.all()[0].name
                
            # Allow access if group is in list OR if user is root superuser
            if group in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden(
                    "<h1>Security Override Blocked</h1>"
                    "<p>Your identity node lacks the clearance level for this module.</p>"
                )
        return wrapper_func
    return decorator