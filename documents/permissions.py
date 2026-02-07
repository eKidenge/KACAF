from rest_framework import permissions


class CanAccessDocument(permissions.BasePermission):
    """
    Custom permission to check if user can access a document based on access level.
    """
    
    def has_permission(self, request, view):
        # Allow all authenticated users to list/view documents
        # Actual access control happens in get_queryset and retrieve methods
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Staff and executive members can access everything
        if user.is_staff or user.user_type == 'executive':
            return True
        
        # Public documents are accessible to all
        if obj.access_level == 'public':
            return True
        
        # Member documents require authentication
        if obj.access_level == 'member' and user.is_authenticated:
            return True
        
        # Executive documents require executive membership
        if obj.access_level == 'executive' and user.user_type == 'executive':
            return True
        
        # Confidential documents require specific permissions
        if obj.access_level == 'confidential':
            # Check if user is owner, creator, or approver
            if user in [obj.owner, obj.created_by, obj.approved_by]:
                return True
        
        return False