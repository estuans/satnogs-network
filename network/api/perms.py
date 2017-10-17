from rest_framework import permissions


class SafeMethodsOnlyPermission(permissions.BasePermission):
    """Anyone can access non-destructive methods (like GET and HEAD)"""
    def has_permission(self, request, view):
        return self.has_object_permission(request, view)

    def has_object_permission(self, request, view, obj=None):
        return request.method in permissions.SAFE_METHODS


class StationOwnerCanEditPermission(permissions.BasePermission):
    """Only the owner can edit station jobs"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated() and request.user == obj.ground_station.owner:
            return True
        else:
            return False
