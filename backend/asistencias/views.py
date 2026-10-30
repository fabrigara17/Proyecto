from django.db import transaction
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from academico.models import VinculoFamiliar
from users.models import ROLES_DIRECCION, Rol, es_direccion
from users.permissions import EsAdminOPreceptor, EsDocenteOPreceptor, EstaAutenticado
from .models import Asistencia, DiaSinClases, Estado, HorarioClase, NotaClase
from .serializers import (
    AsistenciaSerializer, DiaSinClasesSerializer, HorarioClaseSerializer,
    NotaClaseSerializer, TomarAsistenciaSerializer,
)


def _parse_fecha(valor):
    try:
        f = parse_date(valor)
    except ValueError:
        f = None
    if f is None:
        raise ValidationError({'fecha': 'Formato inválido, usar YYYY-MM-DD.'})
    return f


def _parse_id(valor, nombre):
    try:
        return int(valor)
    except ValueError:
        raise ValidationError({nombre: 'Debe ser un número.'})


class AsistenciaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Consulta de asistencias. Se cargan y corrigen solo con la acción "tomar", y solo el mismo día."""
    serializer_class = AsistenciaSerializer

    def get_permissions(self):
        if self.action == 'tomar':
            return [EsDocenteOPreceptor()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = Asistencia.objects.select_related('alumno', 'curso', 'clase', 'materia_curso__materia')

        if user.rol in ROLES_DIRECCION:
            return qs.none()  # el administrador no ve las asistencias de los alumnos
        elif user.is_superuser:
            pass
        elif user.rol == Rol.DOCENTE:
            # El docente ve la asistencia de sus materias
            qs = qs.filter(materia_curso__asignaciones__docente=user).distinct()
        elif user.rol == Rol.PRECEPTOR:
            qs = qs.filter(curso__preceptores__preceptor=user)
        elif user.rol == Rol.ALUMNO:
            qs = qs.filter(alumno=user)
        elif user.rol == Rol.FAMILIA:
            qs = qs.filter(
                alumno__in=VinculoFamiliar.objects.filter(tutor=user).values('alumno')
            )
        else:
            return qs.none()

        p = self.request.query_params
        if p.get('fecha'):
            qs = qs.filter(fecha=_parse_fecha(p['fecha']))
        if p.get('curso'):
            qs = qs.filter(curso_id=_parse_id(p['curso'], 'curso'))
        if p.get('clase'):
            qs = qs.filter(clase_id=_parse_id(p['clase'], 'clase'))
        return qs

    @action(detail=False, methods=['post'], url_path='tomar')
    def tomar(self, request):
        """Guarda la asistencia de una clase en un día: crea los registros nuevos y corrige los existentes.
        Solo funciona el mismo día: al terminar, la asistencia queda cerrada."""
        serializer = TomarAsistenciaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        clase = serializer.validated_data['clase']
        fecha = serializer.validated_data['fecha']
                    # Nota de la clase: una por autor, por clase y por día
        
        with transaction.atomic():
            for r in serializer.validated_data['registros']:
                Asistencia.objects.update_or_create(
                    alumno=r['alumno'], clase=clase, fecha=fecha,
                    defaults={
                        'curso': clase.curso,
                        'materia_curso': clase.materia_curso,
                        'estado': r['estado'],
                        'presente': r['estado'] != Estado.AUSENTE,
                        'registrado_por': request.user,
                    },
                )
            nota = serializer.validated_data.get('nota')
            if nota is not None:
                nota = nota.strip()
                if nota:
                    NotaClase.objects.update_or_create(
                        clase=clase, fecha=fecha, autor=request.user, 
                        defaults={'texto': nota},
                    )
                else:
                    NotaClase.objects.filter(
                        clase=clase, fecha=fecha, autor=request.user
                        ).delete()
                

        registros = self.get_queryset().filter(clase=clase, fecha=fecha)
        return Response(AsistenciaSerializer(registros, many=True, context={'request': request}).data)

class NotaClaseViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Notas de clase. Solo las ve el personal (docente de la materia, preceptor del curso).
    Se guardan con la acción "tomar" de asistencias, no se crean desde acá."""
    serializer_class = NotaClaseSerializer
    permission_classes = [EsDocenteOPreceptor]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        qs = NotaClase.objects.select_related('autor')

        if user.is_superuser:
            pass
        elif user.rol == Rol.DOCENTE:
            qs = qs.filter(clase__materia_curso__asignaciones__docente=user).distinct()
        elif user.rol == Rol.PRECEPTOR:
            qs = qs.filter(clase__curso__preceptores__preceptor=user)
        else:
            return qs.none()

        p = self.request.query_params
        if p.get('clase'):
            qs = qs.filter(clase_id=_parse_id(p['clase'], 'clase'))
        if p.get('fecha'):
            qs = qs.filter(fecha=_parse_fecha(p['fecha']))
        return qs


    
class HorarioClaseViewSet(viewsets.ModelViewSet):
    """Horario semanal de cada curso. Lo arma el preceptor del curso (o conducción)."""
    serializer_class = HorarioClaseSerializer
    pagination_class = None  # listados acotados por curso, se devuelven como lista

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [EsAdminOPreceptor()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = (
            HorarioClase.objects
            .select_related('curso', 'materia_curso__materia')
            .prefetch_related('materia_curso__asignaciones__docente')
        )

        if es_direccion(user):
            pass
        elif user.rol == Rol.PRECEPTOR:
            qs = qs.filter(curso__preceptores__preceptor=user)
        elif user.rol == Rol.DOCENTE:
            # El docente ve las clases de sus materias
            qs = qs.filter(materia_curso__asignaciones__docente=user).distinct()
        elif user.rol == Rol.ALUMNO:
            qs = qs.filter(curso__inscripciones__alumno=user).distinct()
        elif user.rol == Rol.FAMILIA:
            qs = qs.filter(
                curso__inscripciones__alumno__in=VinculoFamiliar.objects.filter(tutor=user).values('alumno')
            ).distinct()
        else:
            return qs.none()

        p = self.request.query_params
        if p.get('curso'):
            qs = qs.filter(curso_id=_parse_id(p['curso'], 'curso'))
        if p.get('dia_semana'):
            qs = qs.filter(dia_semana=_parse_id(p['dia_semana'], 'dia_semana'))
        return qs


class DiaSinClasesViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """Días sin clases. Sin edición: si hay un error, se borra y se vuelve a cargar."""
    serializer_class = DiaSinClasesSerializer

    def get_permissions(self):
        # Consultarlos puede cualquiera (el docente lo necesita para saber si hay clases);
        # cargarlos o quitarlos, solo conducción y preceptores
        if self.action in ('list', 'retrieve'):
            return [EstaAutenticado()]
        return [EsAdminOPreceptor()]

    def get_queryset(self):
        user = self.request.user
        qs = DiaSinClases.objects.select_related('curso')
        if es_direccion(user):
            pass
        elif user.rol == Rol.PRECEPTOR:
            # El preceptor ve los de todo el colegio y los de sus cursos
            qs = qs.filter(Q(curso__isnull=True) | Q(curso__preceptores__preceptor=user)).distinct()
        elif user.rol == Rol.DOCENTE:
            qs = qs.filter(Q(curso__isnull=True) | Q(curso__plan__asignaciones__docente=user)).distinct()
        else:
            qs = qs.filter(curso__isnull=True)

        p = self.request.query_params
        if p.get('fecha'):
            qs = qs.filter(fecha=_parse_fecha(p['fecha']))
        if p.get('curso'):
            curso_id = _parse_id(p['curso'], 'curso')
            # Los que afectan a ese curso: los suyos y los de todo el colegio
            qs = qs.filter(Q(curso_id=curso_id) | Q(curso__isnull=True))
        return qs

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.curso_id is None and not (user.is_superuser or user.rol == Rol.ADMIN):
            raise PermissionDenied('Solo el administrador puede quitar un día sin clases de todo el colegio.')
        instance.delete()