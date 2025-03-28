from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission: Only admins can perform write operations,
    others can only read (GET requests).
    """

    def has_permission(self, request, view):
        # Allow unauthenticated users to read-only access
        if request.method in SAFE_METHODS:
            return True
        # Only allow to write access for authenticated admin users
        return request.user.is_authenticated and request.user.is_staff
