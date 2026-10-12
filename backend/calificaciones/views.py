from rest_framework import viewsets

from academico.models import VinculoFamiliar
from notificaciones.models import Notificacion
from users.models import Rol
from users.permissions import EsDocente, EstaAutenticado
from .models import Calificacion
from .serializers import CalificacionSerializer


class CalificacionesViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EsDocente()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = Calificacion.objects.select_related('alumno', 'materia', 'curso', 'docente')
        if user.is_superuser or user.rol in (Rol.ADMIN, Rol.PRECEPTOR):
            return qs
        if user.rol == Rol.DOCENTE:
            return qs.filter(docente=user)
        if user.rol == Rol.ALUMNO:
            return qs.filter(alumno=user)
        if user.rol == Rol.FAMILIA:
            return qs.filter(
                alumno__in=VinculoFamiliar.objects.filter(tutor=user).values('alumno')
            )
        return qs.none()

    def perform_create(self, serializer):
        cal = serializer.save(docente=self.request.user)
        Notificacion.objects.create(
            usuario=cal.alumno,
            mensaje=f"Nueva nota en {cal.materia}: {cal.nota}",
        )