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
from .models import Asistencia, DiaSinClases
from .serializers import AsistenciaSerializer, DiaSinClasesSerializer, TomarAsistenciaSerializer


def _parse_fecha(valor):
    try:
        f = parse_date(valor)
    except ValueError:
        f = None
    if f is None:
        raise ValidationError({'fecha': 'Formato inválido, usar YYYY-MM-DD.'})
    return f


class AsistenciaViewSet(viewsets.ModelViewSet):
    serializer_class = AsistenciaSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'lote', 'tomar'):
            return [EsDocenteOPreceptor()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = Asistencia.objects.select_related('alumno', 'curso')

        if user.rol in ROLES_DIRECCION:
            return qs.none()  # el administrador no ve las asistencias de los alumnos
        elif user.is_superuser:
            pass
        elif user.rol == Rol.DOCENTE:
            qs = qs.filter(curso__plan__asignaciones__docente=user).distinct()
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

        # El docente solo corrige lo que cargó él; el preceptor corrige cualquier registro de sus cursos
        if (self.action in ('update', 'partial_update', 'destroy')
                and user.rol == Rol.DOCENTE and not user.is_superuser):
            qs = qs.filter(registrado_por=user)

        p = self.request.query_params
        if p.get('fecha'):
            qs = qs.filter(fecha=_parse_fecha(p['fecha']))
        if p.get('curso'):
            qs = qs.filter(curso_id=p['curso'])
        return qs

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    @action(detail=False, methods=['post'], url_path='lote')
    def lote(self, request):
        if not isinstance(request.data, list):
            raise ValidationError('Se esperaba una lista de asistencias.')
        claves = [
            (str(i.get('alumno')), str(i.get('curso')), str(i.get('fecha')))
            for i in request.data if isinstance(i, dict)
        ]
        if len(claves) != len(set(claves)):
            raise ValidationError('Hay registros repetidos (mismo alumno, curso y fecha) en el lote.')
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(registrado_por=request.user)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['post'], url_path='tomar')
    def tomar(self, request):
        """Guarda la asistencia de un curso en un día: crea los registros nuevos y corrige los existentes."""
        serializer = TomarAsistenciaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        curso = serializer.validated_data['curso']
        fecha = serializer.validated_data['fecha']

        with transaction.atomic():
            for r in serializer.validated_data['registros']:
                Asistencia.objects.update_or_create(
                    alumno=r['alumno'], curso=curso, fecha=fecha,
                    defaults={'presente': r['presente'], 'registrado_por': request.user},
                )

        registros = Asistencia.objects.filter(curso=curso, fecha=fecha).select_related('alumno', 'curso')
        return Response(AsistenciaSerializer(registros, many=True, context={'request': request}).data)


class DiaSinClasesViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """Días sin clases. Sin edición: si hay un error, se borra y se vuelve a cargar."""
    serializer_class = DiaSinClasesSerializer
    permission_classes = [EsAdminOPreceptor]

    def get_queryset(self):
        user = self.request.user
        qs = DiaSinClases.objects.select_related('curso')
        if not es_direccion(user):
            # El preceptor ve los de todo el colegio y los de sus cursos
            qs = qs.filter(Q(curso__isnull=True) | Q(curso__preceptores__preceptor=user))

        p = self.request.query_params
        if p.get('fecha'):
            qs = qs.filter(fecha=_parse_fecha(p['fecha']))
        if p.get('curso'):
            try:
                curso_id = int(p['curso'])
            except ValueError:
                raise ValidationError({'curso': 'Debe ser un número.'})
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