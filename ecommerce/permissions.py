from rest_framework import permissions


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Allows access to managers and admins.
    Managers only see their store's data (handled in queryset filtering).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'staff_profile'):
            return False

        return request.user.staff_profile.role in ['manager', 'admin']


class IsAdmin(permissions.BasePermission):
    """Allows access only to admins."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'staff_profile'):
            return False

        return request.user.staff_profile.role == 'admin'


class IsStoreManager(permissions.BasePermission):
    """Allows access to managers of the same store as the object."""
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'staff_profile'):
            return False

        profile = request.user.staff_profile
        if profile.role == 'admin':
            return True

        if profile.role == 'manager':
            store = getattr(obj, 'store', None)
            if store:
                return store == profile.store
            return False

        return False