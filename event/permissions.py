from rest_framework import permissions

class IsEventCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_anonymous or request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return False
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.profile==obj.creator