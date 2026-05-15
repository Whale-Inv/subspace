from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Только автор может редактировать/удалять
    """

    def has_object_permission(self, request, view, obj):
        # GET, HEAD, OPTIONS — разрешены всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # PUT, PATCH, DELETE — только автору
        return obj.author == request.user
