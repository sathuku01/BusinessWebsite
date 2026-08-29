from .cart import get_cart_summary


def cart_summary(request):
    return {'cart_summary': get_cart_summary(request)}


def staff_context(request):
    """Add staff role flags to all templates."""
    context = {
        'is_manager': False,
        'is_admin': False,
        'user_store': None,
    }

    if request.user.is_authenticated and hasattr(request.user, 'staff_profile'):
        profile = request.user.staff_profile
        if profile.is_active:
            context['is_manager'] = profile.role in ['manager', 'admin']
            context['is_admin'] = profile.role == 'admin'
            context['user_store'] = profile.store

    return context