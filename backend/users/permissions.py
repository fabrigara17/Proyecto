"""
Control de acceso basado en roles (RBAC) para Libreta Digital — DRF.
Docs: https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
"""
from rest_framework.permissions import BasePermission

from .models import Rol


class EstaAutenticado(BasePermission):
    """Autenticado y sin cambio de contraseña pendiente."""

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if u.debe_cambiar_password:
            self.message = 'Debés cambiar tu contraseña antes de continuar.'
            return False
        return True


class TieneRol(EstaAutenticado):
    roles_permitidos: tuple = ()

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        u = request.user
        if u.is_superuser or u.rol in self.roles_permitidos:
            return True
        self.message = 'No tenés permiso para realizar esta acción.'
        return False


class EsAdmin(TieneRol):
    roles_permitidos = (Rol.ADMIN,)

class EsConduccion(TieneRol):
    """Equipo de conducción (y el rol de desarrollo, que conserva todos los permisos)."""
    roles_permitidos = (Rol.ADMIN, Rol.CONDUCCION)

class EsDocente(TieneRol):
    roles_permitidos = (Rol.DOCENTE,)

class EsPreceptor(TieneRol):
    roles_permitidos = (Rol.PRECEPTOR,)

class EsFamilia(TieneRol):
    roles_permitidos = (Rol.FAMILIA,)

class EsAlumno(TieneRol):
    roles_permitidos = (Rol.ALUMNO,)

class EsDocenteOPreceptor(TieneRol):
    roles_permitidos = (Rol.DOCENTE, Rol.PRECEPTOR)

class EsDocenteOAdmin(TieneRol):
    roles_permitidos = (Rol.DOCENTE, Rol.ADMIN)

class EsConduccionOPreceptor(TieneRol):
    roles_permitidos = (Rol.ADMIN, Rol.CONDUCCION, Rol.PRECEPTOR)

# Nombre anterior, para no tocar los archivos que ya lo importan
EsAdminOPreceptor = EsConduccionOPreceptor

class PuedeGestionarUsuarios(TieneRol):
    """Quiénes pueden entrar a la gestión de usuarios. Qué roles puede tocar cada uno lo decide roles_gestionables()."""
    roles_permitidos = (Rol.ADMIN, Rol.CONDUCCION, Rol.PRECEPTOR)