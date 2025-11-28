from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def require_role(*roles):
    """
    Decorator to restrict view access to users with specific roles.
    
    Usage:
        @require_role('admin')
        @require_role('admin', 'staff')
    
    Args:
        *roles: One or more role names that are allowed to access the view
    
    Raises:
        PermissionDenied: If user doesn't have one of the required roles
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                raise PermissionDenied("User does not have a role assigned.")
            
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied(
                    f"Access denied. Required role: {' or '.join(roles)}. Your role: {request.user.role}"
                )
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to restrict view access to admin users only.
    
    Usage:
        @admin_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            raise PermissionDenied("User does not have a role assigned.")
        
        if request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied("Access denied. Admin access required.")
    return wrapper


def staff_required(view_func):
    """
    Decorator to restrict view access to staff and admin users.
    
    Usage:
        @staff_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            raise PermissionDenied("User does not have a role assigned.")
        
        if request.user.role in ['admin', 'staff']:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied("Access denied. Staff or admin access required.")
    return wrapper


def borrower_or_staff_required(view_func):
    """
    Decorator to restrict view access to authenticated users with any role.
    This is essentially the same as @login_required but checks for role existence.
    
    Usage:
        @borrower_or_staff_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role'):
            raise PermissionDenied("User does not have a role assigned.")
        
        return view_func(request, *args, **kwargs)
    return wrapper
