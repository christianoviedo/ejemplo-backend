from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = 'Se requiere rol de administrador.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsGestorOrAdmin(BasePermission):
    message = 'Se requiere rol de gestor o administrador.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('gestor', 'admin')
        )
