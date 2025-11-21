from rest_framework import permissions

class IsOrganizerAndOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_organizer
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.host == request.user
        return True
