from rest_framework import permissions
from accounts.permissions import IsChairperson


class IsTreasurer(permissions.BasePermission):
    """
    Permission to check if user is the treasurer.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is treasurer in executive committee
        from accounts.models import ExecutiveCommittee
        return ExecutiveCommittee.objects.filter(
            user=request.user, 
            position='treasurer',
            is_active=True
        ).exists() or request.user.is_superuser


class IsFinancialManager(permissions.BasePermission):
    """
    Permission for users who can manage finances (Treasurer, Chairperson, Admin).
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        from accounts.models import ExecutiveCommittee
        return (
            ExecutiveCommittee.objects.filter(
                user=request.user,
                position__in=['treasurer', 'chairperson'],
                is_active=True
            ).exists() or 
            request.user.is_staff or 
            request.user.is_superuser
        )