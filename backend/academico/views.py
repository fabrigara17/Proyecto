from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, ProtectedError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from asistencias.models import Asistencia
from calificaciones.models import Calificacion
from materiales.models import Material
from users.models import Rol, es_direccion
from users.permissions import EsAdmin, EsConduccion, EstaAutenticado
from .models import (
    Curso, Materia, MateriaCurso, Inscripcion, AsignacionDocente,
    AsignacionPreceptor, VinculoFamiliar,
)
from .serializers import (
    CursoSerializer, MateriaSerializer, MateriaCursoSerializer,
    MateriaCursoDetalleSerializer, AlumnoSerializer, InscripcionSerializer,
    AsignacionDocenteSerializer, AsignacionPreceptorSerializer,
    VinculoFamiliarSerializer,
)

Usuario = get_user_model()


def _ve_todo(user):
    return es_direccion(user)


def _alumnos_a_cargo(user):
    return VinculoFamiliar.objects.filter(tutor=user).values('alumno')


def _nombre(u):
    return u.get_full_name() or u.username


def _borrar(instance, mensaje):
    try:
        instance.delete()
    except ProtectedError:
        raise ValidationError(mensaje)


class SoloConduccionSalvoAcciones:
    """Todo es para el equipo de conducción, salvo las acciones listadas en `acciones_libres`,
    que hacen sus propios controles por rol."""
    acciones_libres = ()

    def get_permissions(self):
        if self.action in self.acciones_libres:
            return [EstaAutenticado()]
        return [EsConduccion()]


class CursoViewSet(SoloConduccionSalvoAcciones, viewsets.ModelViewSet):
    queryset = Curso.objects.annotate(
        cant_alumnos=Count('inscripciones', distinct=True),
        cant_materias=Count('plan', distinct=True),
    )
    serializer_class = CursoSerializer
    acciones_libres = ('mis_cursos', 'alumnos')

    @action(detail=False, methods=['get'], url_path='mis-cursos')
    def mis_cursos(self, request):
        user = request.user
        if _ve_todo(user):
            qs = Curso.objects.all()
        elif user.rol == Rol.DOCENTE:
            qs = Curso.objects.filter(plan__asignaciones__docente=user).distinct()
        elif user.rol == Rol.PRECEPTOR:
            qs = Curso.objects.filter(preceptores__preceptor=user)
        elif user.rol == Rol.ALUMNO:
            qs = Curso.objects.filter(inscripciones__alumno=user).distinct()
        elif user.rol == Rol.FAMILIA:
            qs = Curso.objects.filter(
                inscripciones__alumno__in=_alumnos_a_cargo(user)
            ).distinct()
        else:
            qs = Curso.objects.none()
        return Response(CursoSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def alumnos(self, request, pk=None):
        curso = self.get_object()
        user = request.user
        if not _ve_todo(user):
            if user.rol == Rol.DOCENTE:
                tiene_acceso = AsignacionDocente.objects.filter(
                    docente=user, materia_curso__curso=curso
                ).exists()
            elif user.rol == Rol.PRECEPTOR:
                tiene_acceso = AsignacionPreceptor.objects.filter(
                    preceptor=user, curso=curso
                ).exists()
            else:
                tiene_acceso = False
            if not tiene_acceso:
                raise PermissionDenied('No tenés acceso a los alumnos de este curso.')
        alumnos = Usuario.objects.filter(
            inscripciones__curso=curso
        ).order_by('last_name', 'first_name', 'username')
        return Response(AlumnoSerializer(alumnos, many=True).data)

    @action(detail=True, methods=['get'])
    def detalle(self, request, pk=None):
        """Todo lo de un curso en una sola respuesta: materias con sus docentes, preceptores y alumnos."""
        curso = self.get_object()
        plan = (
            MateriaCurso.objects.filter(curso=curso)
            .select_related('materia')
            .prefetch_related(Prefetch(
                'asignaciones',
                queryset=AsignacionDocente.objects.select_related('docente').order_by(
                    'docente__last_name', 'docente__first_name', 'docente__username'),
            ))
            .order_by('materia__nombre')
        )
        preceptores = (
            AsignacionPreceptor.objects.filter(curso=curso).select_related('preceptor')
            .order_by('preceptor__last_name', 'preceptor__first_name', 'preceptor__username')
        )
        inscripciones = (
            Inscripcion.objects.filter(curso=curso).select_related('alumno')
            .order_by('alumno__last_name', 'alumno__first_name', 'alumno__username')
        )
        return Response({
            'id': curso.id,
            'nombre': curso.nombre,
            'anio_cursada': curso.anio_cursada,
            'anio_lectivo': curso.anio_lectivo,
            'materias': [{
                'id': mc.id,
                'materia': mc.materia_id,
                'materia_nombre': mc.materia.nombre,
                'docentes': [
                    {'id': a.id, 'docente': a.docente_id, 'docente_nombre': _nombre(a.docente)}
                    for a in mc.asignaciones.all()
                ],
            } for mc in plan],
            'preceptores': [
                {'id': p.id, 'preceptor': p.preceptor_id, 'preceptor_nombre': _nombre(p.preceptor)}
                for p in preceptores
            ],
            'alumnos': [
                {'id': i.id, 'alumno': i.alumno_id, 'alumno_nombre': _nombre(i.alumno)}
                for i in inscripciones
            ],
        })

    @action(detail=True, methods=['post'], url_path='agregar-materias')
    def agregar_materias(self, request, pk=None):
        """Agrega varias materias al curso de una vez. Las que ya estaban se ignoran."""
        curso = self.get_object()
        ids = request.data.get('materias') if isinstance(request.data, dict) else None
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            raise ValidationError({'materias': 'Se esperaba una lista de números.'})
        materias = list(Materia.objects.filter(id__in=ids))
        if len(materias) != len(set(ids)):
            raise ValidationError({'materias': 'Hay materias que no existen.'})
        ya = set(MateriaCurso.objects.filter(curso=curso).values_list('materia_id', flat=True))
        nuevas = [MateriaCurso(curso=curso, materia=m) for m in materias if m.id not in ya]
        MateriaCurso.objects.bulk_create(nuevas)
        return Response({'agregadas': len(nuevas)})

    def perform_destroy(self, instance):
        if (Asistencia.objects.filter(curso=instance).exists()
                or Calificacion.objects.filter(curso=instance).exists()):
            raise ValidationError('No se puede eliminar el curso: tiene asistencias o notas registradas.')
        if Material.objects.filter(materia_curso__curso=instance).exists():
            raise ValidationError('No se puede eliminar el curso: tiene materiales cargados.')
        _borrar(instance, 'No se puede eliminar el curso: tiene datos asociados.')


class MateriaViewSet(SoloConduccionSalvoAcciones, viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer

    def perform_destroy(self, instance):
        if Calificacion.objects.filter(materia=instance).exists():
            raise ValidationError('No se puede eliminar la materia: tiene notas registradas.')
        if Material.objects.filter(materia_curso__materia=instance).exists():
            raise ValidationError('No se puede eliminar la materia: tiene materiales cargados.')
        _borrar(instance, 'No se puede eliminar la materia: tiene datos asociados.')


class MateriaCursoViewSet(SoloConduccionSalvoAcciones, viewsets.ModelViewSet):
    queryset = MateriaCurso.objects.select_related('curso', 'materia').order_by('curso', 'materia')
    serializer_class = MateriaCursoSerializer
    acciones_libres = ('mis_materias',)

    @action(detail=False, methods=['get'], url_path='mis-materias')
    def mis_materias(self, request):
        user = request.user
        qs = MateriaCurso.objects.select_related('curso', 'materia')
        if _ve_todo(user):
            pass
        elif user.rol == Rol.DOCENTE:
            qs = qs.filter(asignaciones__docente=user)
        elif user.rol == Rol.PRECEPTOR:
            qs = qs.filter(curso__preceptores__preceptor=user)
        elif user.rol == Rol.ALUMNO:
            qs = qs.filter(curso__inscripciones__alumno=user)
        elif user.rol == Rol.FAMILIA:
            qs = qs.filter(curso__inscripciones__alumno__in=_alumnos_a_cargo(user))
        else:
            qs = qs.none()
        qs = qs.distinct().order_by('curso__nombre', 'materia__nombre')
        return Response(MateriaCursoDetalleSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Cada materia en cada curso, con su año de cursada y sus docentes (para la pestaña Materias)."""
        qs = (
            MateriaCurso.objects.select_related('materia', 'curso')
            .prefetch_related(Prefetch(
                'asignaciones',
                queryset=AsignacionDocente.objects.select_related('docente').order_by(
                    'docente__last_name', 'docente__first_name', 'docente__username'),
            ))
            .order_by('materia__nombre', 'curso__anio_cursada', 'curso__nombre')
        )
        return Response([{
            'id': mc.id,
            'materia': mc.materia_id,
            'materia_nombre': mc.materia.nombre,
            'curso': mc.curso_id,
            'curso_nombre': mc.curso.nombre,
            'anio_cursada': mc.curso.anio_cursada,
            'anio_lectivo': mc.curso.anio_lectivo,
            'docentes': [{'id': a.docente_id, 'nombre': _nombre(a.docente)} for a in mc.asignaciones.all()],
        } for mc in qs])

    def perform_destroy(self, instance):
        if Calificacion.objects.filter(curso=instance.curso, materia=instance.materia).exists():
            raise ValidationError('No se puede quitar la materia del curso: ya hay notas cargadas.')
        if Material.objects.filter(materia_curso=instance).exists():
            raise ValidationError('No se puede quitar la materia del curso: tiene materiales cargados.')
        _borrar(instance, 'No se puede quitar la materia del curso: tiene datos asociados.')


# Docentes por materia y preceptores por curso: equipo de conducción
class AsignacionDocenteViewSet(viewsets.ModelViewSet):
    queryset = AsignacionDocente.objects.select_related(
        'docente', 'materia_curso__materia', 'materia_curso__curso',
    ).order_by('id')
    serializer_class = AsignacionDocenteSerializer
    permission_classes = [EsConduccion]


class AsignacionPreceptorViewSet(viewsets.ModelViewSet):
    queryset = AsignacionPreceptor.objects.select_related('preceptor', 'curso').order_by('id')
    serializer_class = AsignacionPreceptorSerializer
    permission_classes = [EsConduccion]


# Inscripciones y vínculos familiares: por ahora solo el rol de desarrollo (pasan a los preceptores en la entrega 3)
class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.select_related('alumno', 'curso').order_by('id')
    serializer_class = InscripcionSerializer
    permission_classes = [EsAdmin]


class VinculoFamiliarViewSet(viewsets.ModelViewSet):
    queryset = VinculoFamiliar.objects.select_related('tutor', 'alumno').order_by('id')
    serializer_class = VinculoFamiliarSerializer

    def get_permissions(self):
        if self.action == 'mis_alumnos':
            return [EstaAutenticado()]
        return [EsAdmin()]

    @action(detail=False, methods=['get'], url_path='mis-alumnos')
    def mis_alumnos(self, request):
        user = request.user
        if user.rol != Rol.FAMILIA and not user.is_superuser:
            raise PermissionDenied('Solo las familias tienen alumnos a cargo.')
        alumnos = Usuario.objects.filter(tutores__tutor=user).order_by('last_name', 'first_name', 'username')
        return Response(AlumnoSerializer(alumnos, many=True).data)