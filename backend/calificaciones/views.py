from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from academico.models import VinculoFamiliar
from notificaciones.models import Notificacion
from users.models import Rol
from users.permissions import EsConduccion, EsDocente, EstaAutenticado
from .models import Calificacion, Etapa
from .serializers import CalificacionSerializer, EtapaSerializer


class EtapaViewSet(viewsets.ModelViewSet):
    """Etapas del año (trimestres, etc.). Todos las ven; solo conducción las crea, abre y cierra."""
    serializer_class = EtapaSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EsConduccion()]
        return [EstaAutenticado()]

    def get_queryset(self):
        qs = Etapa.objects.all()
        anio = self.request.query_params.get('anio_lectivo')
        if anio:
            try:
                qs = qs.filter(anio_lectivo=int(anio))
            except ValueError:
                raise ValidationError({'anio_lectivo': 'Debe ser un número.'})
        return qs

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('No se puede eliminar la etapa: ya tiene notas cargadas. Podés cerrarla en su lugar.')


class CalificacionesViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EsDocente()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = Calificacion.objects.select_related('alumno', 'materia', 'curso', 'etapa', 'docente')
        if user.is_superuser or user.rol in (Rol.ADMIN, Rol.PRECEPTOR):
            pass
        elif user.rol == Rol.DOCENTE:
            qs = qs.filter(docente=user)
        elif user.rol == Rol.ALUMNO:
            qs = qs.filter(alumno=user)
        elif user.rol == Rol.FAMILIA:
            qs = qs.filter(
                alumno__in=VinculoFamiliar.objects.filter(tutor=user).values('alumno')
            )
        else:
            return qs.none()

        # Filtros opcionales: ?curso=1&materia=2&etapa=3&alumno=4
        for campo in ('curso', 'materia', 'etapa', 'alumno'):
            valor = self.request.query_params.get(campo)
            if valor:
                try:
                    qs = qs.filter(**{f'{campo}_id': int(valor)})
                except ValueError:
                    raise ValidationError({campo: 'Debe ser un número.'})
        return qs

    def perform_create(self, serializer):
        cal = serializer.save(docente=self.request.user)
        Notificacion.objects.create(
            usuario=cal.alumno,
            mensaje=f"Nueva nota en {cal.materia}: {cal.nota}",
        )

    def perform_destroy(self, instance):
        etapa = instance.etapa
        if etapa is not None and not self.request.user.is_superuser and not etapa.esta_abierta:
            raise PermissionDenied(f'La etapa "{etapa.nombre}" está cerrada: no se pueden eliminar notas.')
        instance.delete()