from rest_framework import permissions

# ---------------------------
# Only owner can update/delete
# ---------------------------
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for owner
        return obj.user == request.user


# ---------------------------
# Chairperson-only actions
# ---------------------------
class IsChairperson(permissions.BasePermission):
    """
    Custom permission for Chairperson only
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "user_type", None) == 'chairperson'


# ---------------------------
# Executive Committee member
# ---------------------------
class IsExecutiveMember(permissions.BasePermission):
    """
    Custom permission for executive members
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "user_type", None) == 'executive'
