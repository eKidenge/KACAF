from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj == request.user


class IsExecutiveMember(permissions.BasePermission):
    """
    Permission to check if user is an executive committee member.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.user_type == 'executive' or 
            request.user.is_staff
        )


class IsChairperson(permissions.BasePermission):
    """
    Permission to check if user is the chairperson.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is chairperson in executive committee
        from .models import ExecutiveCommittee
        return ExecutiveCommittee.objects.filter(
            user=request.user, 
            position='chairperson',
            is_active=True
        ).exists() or request.user.is_superuser