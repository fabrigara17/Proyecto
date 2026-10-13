from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Avg, Count, Prefetch, ProtectedError, Q
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import BasePermission

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

def _redondear(valor, decimales=2):
    return None if valor is None else round(float(valor), decimales)


def _porcentaje(parte, total):
    return None if not total else round(parte * 100 / total, 1)


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
            'turno': curso.turno,
            'turno_display': curso.get_turno_display(),
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


    @action(detail=True, methods=['get'])
    def seguimiento(self, request, pk=None):
        """Asistencias, aprobación y estadísticas de un curso (equipo de conducción)."""
        curso = self.get_object()
        minima = getattr(settings, 'NOTA_APROBACION', 6)

        alumnos = list(
            Usuario.objects.filter(inscripciones__curso=curso)
            .order_by('last_name', 'first_name', 'username')
        )
        ids = [a.id for a in alumnos]
        nombres = {a.id: _nombre(a) for a in alumnos}

        # ---- Asistencias ----
        registros = Asistencia.objects.filter(curso=curso, alumno_id__in=ids)
        por_alumno = {
            f['alumno']: f
            for f in registros.values('alumno').annotate(
                total=Count('id'), presentes=Count('id', filter=Q(presente=True)),
            ).order_by()
        }
        asistencia_alumnos = []
        for a in alumnos:
            f = por_alumno.get(a.id, {'total': 0, 'presentes': 0})
            asistencia_alumnos.append({
                'alumno': a.id,
                'alumno_nombre': nombres[a.id],
                'presentes': f['presentes'],
                'ausentes': f['total'] - f['presentes'],
                'porcentaje': _porcentaje(f['presentes'], f['total']),
            })
        # Primero los de menor asistencia; los que no tienen registros, al final
        asistencia_alumnos.sort(key=lambda x: (
            x['porcentaje'] is None,
            x['porcentaje'] if x['porcentaje'] is not None else 0,
            x['alumno_nombre'],
        ))
        totales = registros.aggregate(
            total=Count('id'),
            presentes=Count('id', filter=Q(presente=True)),
            dias=Count('fecha', distinct=True),
        )
        asistencia = {
            'dias_registrados': totales['dias'],
            'presentes': totales['presentes'],
            'ausentes': totales['total'] - totales['presentes'],
            'porcentaje': _porcentaje(totales['presentes'], totales['total']),
            'por_alumno': asistencia_alumnos,
        }

        # ---- Aprobación ----
        notas = Calificacion.objects.filter(curso=curso, alumno_id__in=ids)
        promedios = list(notas.values('alumno', 'materia').annotate(promedio=Avg('nota')).order_by())
        por_materia_notas = {
            f['materia']: f
            for f in notas.values('materia').annotate(
                promedio=Avg('nota'), cantidad=Count('id'),
            ).order_by()
        }
        evaluados, aprobados, desaprobadas = {}, {}, {}
        for p in promedios:
            m, al = p['materia'], p['alumno']
            evaluados[m] = evaluados.get(m, 0) + 1
            if p['promedio'] >= minima:
                aprobados[m] = aprobados.get(m, 0) + 1
            else:
                desaprobadas[al] = desaprobadas.get(al, 0) + 1

        por_materia = []
        plan = MateriaCurso.objects.filter(curso=curso).select_related('materia').order_by('materia__nombre')
        for mc in plan:
            s = por_materia_notas.get(mc.materia_id)
            n_eval = evaluados.get(mc.materia_id, 0)
            n_apr = aprobados.get(mc.materia_id, 0)
            por_materia.append({
                'materia': mc.materia_id,
                'materia_nombre': mc.materia.nombre,
                'cantidad_notas': s['cantidad'] if s else 0,
                'promedio': _redondear(s['promedio']) if s else None,
                'evaluados': n_eval,
                'aprobados': n_apr,
                'desaprobados': n_eval - n_apr,
                'porcentaje_aprobacion': _porcentaje(n_apr, n_eval),
            })
        en_riesgo = sorted(
            (
                {'alumno': al, 'alumno_nombre': nombres.get(al, ''), 'materias_desaprobadas': n}
                for al, n in desaprobadas.items()
            ),
            key=lambda x: (-x['materias_desaprobadas'], x['alumno_nombre']),
        )
        aprobacion = {
            'nota_minima': minima,
            'por_materia': por_materia,
            'alumnos_en_riesgo': en_riesgo,
        }

        # ---- Estadísticas ----
        por_mes = (
            registros.annotate(mes=TruncMonth('fecha')).values('mes')
            .annotate(total=Count('id'), presentes=Count('id', filter=Q(presente=True)))
            .order_by('mes')
        )
        notas_resumen = notas.aggregate(
            promedio=Avg('nota'),
            bajo=Count('id', filter=Q(nota__lt=4)),
            medio_bajo=Count('id', filter=Q(nota__gte=4, nota__lt=6)),
            medio_alto=Count('id', filter=Q(nota__gte=6, nota__lt=8)),
            alto=Count('id', filter=Q(nota__gte=8)),
        )
        estadisticas = {
            'total_alumnos': len(alumnos),
            'total_materias': len(por_materia),
            'promedio_general': _redondear(notas_resumen['promedio']),
            'asistencia_por_mes': [
                {
                    'mes': f['mes'].strftime('%Y-%m'),
                    'porcentaje': _porcentaje(f['presentes'], f['total']),
                    'registros': f['total'],
                }
                for f in por_mes
            ],
            'distribucion_notas': [
                {'rango': '1 a 3', 'cantidad': notas_resumen['bajo']},
                {'rango': '4 a 5', 'cantidad': notas_resumen['medio_bajo']},
                {'rango': '6 a 7', 'cantidad': notas_resumen['medio_alto']},
                {'rango': '8 a 10', 'cantidad': notas_resumen['alto']},
            ],
        }

        return Response({
            'asistencia': asistencia,
            'aprobacion': aprobacion,
            'estadisticas': estadisticas,
        })

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


def _es_admin(user):
    return user.is_superuser or user.rol == Rol.ADMIN


class EsAdminOPreceptor(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (_es_admin(u) or u.rol == Rol.PRECEPTOR))


def _cursos_del_preceptor(user):
    return AsignacionPreceptor.objects.filter(preceptor=user).values('curso')


class InscripcionViewSet(viewsets.ModelViewSet):
    """Admin: todo. Preceptor: solo inscripciones de los cursos que tiene a cargo."""
    serializer_class = InscripcionSerializer
    permission_classes = [EsAdminOPreceptor]
    pagination_class = None  # listados acotados por curso, se devuelven como lista

    def get_queryset(self):
        user = self.request.user
        qs = Inscripcion.objects.select_related('alumno', 'curso').order_by(
            'alumno__last_name', 'alumno__first_name', 'alumno__username')
        if not _es_admin(user):
            qs = qs.filter(curso__in=_cursos_del_preceptor(user))
        curso = self.request.query_params.get('curso')
        if curso and curso.isdigit():
            qs = qs.filter(curso_id=curso)
        return qs

    def _controlar_curso(self, curso):
        user = self.request.user
        if not _es_admin(user) and not AsignacionPreceptor.objects.filter(
                preceptor=user, curso=curso).exists():
            raise PermissionDenied('Ese curso no está a tu cargo.')

    def perform_create(self, serializer):
        self._controlar_curso(serializer.validated_data['curso'])
        serializer.save()

    def perform_update(self, serializer):
        self._controlar_curso(serializer.validated_data.get('curso', serializer.instance.curso))
        serializer.save()

    def perform_destroy(self, instance):
        _borrar(instance, 'No se puede quitar al alumno del curso: tiene datos asociados.')


class VinculoFamiliarViewSet(viewsets.ModelViewSet):
    """Admin: todo. Preceptor: solo vínculos de alumnos inscriptos en sus cursos."""
    serializer_class = VinculoFamiliarSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action == 'mis_alumnos':
            return [EstaAutenticado()]
        return [EsAdminOPreceptor()]

    def get_queryset(self):
        user = self.request.user
        qs = VinculoFamiliar.objects.select_related('tutor', 'alumno').order_by(
            'alumno__last_name', 'alumno__first_name', 'tutor__last_name', 'tutor__first_name')
        if not _es_admin(user):
            alumnos = Inscripcion.objects.filter(
                curso__in=_cursos_del_preceptor(user)).values('alumno')
            qs = qs.filter(alumno__in=alumnos)
        curso = self.request.query_params.get('curso')
        if curso and curso.isdigit():
            alumnos_curso = Inscripcion.objects.filter(curso_id=curso).values('alumno')
            qs = qs.filter(alumno__in=alumnos_curso)
        return qs

    def _controlar_alumno(self, alumno):
        user = self.request.user
        if not _es_admin(user) and not Inscripcion.objects.filter(
                alumno=alumno, curso__in=_cursos_del_preceptor(user)).exists():
            raise PermissionDenied('Ese alumno no está en un curso a tu cargo.')

    def perform_create(self, serializer):
        self._controlar_alumno(serializer.validated_data['alumno'])
        serializer.save()

    def perform_update(self, serializer):
        self._controlar_alumno(serializer.validated_data.get('alumno', serializer.instance.alumno))
        serializer.save()

    @action(detail=False, methods=['get'], url_path='mis-alumnos')
    def mis_alumnos(self, request):
        user = request.user
        if user.rol != Rol.FAMILIA and not user.is_superuser:
            raise PermissionDenied('Solo las familias tienen alumnos a cargo.')
        alumnos = Usuario.objects.filter(tutores__tutor=user).order_by('last_name', 'first_name', 'username')
        return Response(AlumnoSerializer(alumnos, many=True).data)