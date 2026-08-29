from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def manager_required(view_func):
    """Requires user to be manager or admin with active staff profile."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.is_active:
            messages.error(request, 'Access denied. Staff profile required.')
            return redirect('dashboard')

        if request.user.staff_profile.role not in ['manager', 'admin']:
            messages.error(request, 'Access denied. Manager or Admin role required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return wrapped


def admin_required(view_func):
    """Requires user to be admin with active staff profile."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.is_active:
            messages.error(request, 'Access denied. Staff profile required.')
            return redirect('dashboard')

        if request.user.staff_profile.role != 'admin':
            messages.error(request, 'Access denied. Admin role required.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return wrapped


def store_manager_required(view_func):
    """Requires manager/admin AND stores match (for object-level views)."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        if not hasattr(request.user, 'staff_profile') or not request.user.staff_profile.is_active:
            messages.error(request, 'Access denied.')
            return redirect('dashboard')

        profile = request.user.staff_profile
        if profile.role not in ['manager', 'admin']:
            messages.error(request, 'Manager or Admin role required.')
            return redirect('dashboard')

        if profile.role == 'admin':
            return view_func(request, *args, **kwargs)

        return view_func(request, *args, **kwargs)
    return wrapped