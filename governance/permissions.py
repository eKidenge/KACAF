from rest_framework import permissions
from accounts.permissions import IsChairperson, IsExecutiveMember


class IsSubjectOfDisciplinaryAction(permissions.BasePermission):
    """
    Permission to check if user is the subject of a disciplinary action.
    """
    
    def has_permission(self, request, view):
        if view.action == 'appeal':
            return True
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # User can view their own disciplinary actions
        if request.method in permissions.SAFE_METHODS:
            return obj.member == request.user or request.user.user_type == 'executive'
        
        # User can only appeal their own actions
        if view.action == 'appeal':
            return obj.member == request.user
        
        return False