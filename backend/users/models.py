from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'  # rol de desarrollo: conserva todos los permisos
    CONDUCCION = 'CONDUCCION', 'Equipo de Conducción'
    DOCENTE = 'DOCENTE', 'Docente'
    PRECEPTOR = 'PRECEPTOR', 'Preceptor'
    FAMILIA = 'FAMILIA', 'Familia'
    ALUMNO = 'ALUMNO', 'Alumno'


# Quiénes dirigen la institución
ROLES_DIRECCION = (Rol.ADMIN, Rol.CONDUCCION)


def es_direccion(user):
    return bool(getattr(user, 'is_superuser', False)) or getattr(user, 'rol', None) in ROLES_DIRECCION


def roles_gestionables(user):
    """Roles de usuario que esta persona puede ver, crear y editar."""
    if user.is_superuser or user.rol == Rol.ADMIN:
        return tuple(Rol.values)
    if user.rol == Rol.CONDUCCION:
        return (Rol.DOCENTE, Rol.PRECEPTOR, Rol.CONDUCCION)
    if user.rol == Rol.PRECEPTOR:
        return (Rol.ALUMNO, Rol.FAMILIA)
    return ()


class Usuario(AbstractUser):
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.FAMILIA)
    debe_cambiar_password = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"