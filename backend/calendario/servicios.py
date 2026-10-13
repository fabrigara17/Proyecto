from django.db.models import Q

from academico.models import AsignacionPreceptor, Curso, Inscripcion, MateriaCurso, VinculoFamiliar
from users.models import Rol, Usuario, es_direccion
from .models import DestinoEvento

T = DestinoEvento.Tipo

ROLES_DE_CATEGORIA = (Rol.CONDUCCION, Rol.DOCENTE, Rol.PRECEPTOR, Rol.FAMILIA, Rol.ALUMNO)
ROLES_DE_CURSO = (Rol.ALUMNO, Rol.FAMILIA, Rol.DOCENTE, Rol.PRECEPTOR)

# Cómo se nombra cada grupo en pantalla
PLURAL = {
    Rol.CONDUCCION: 'Equipo de conducción',
    Rol.DOCENTE: 'Docentes',
    Rol.PRECEPTOR: 'Preceptores',
    Rol.FAMILIA: 'Familias',
    Rol.ALUMNO: 'Alumnos',
}


def es_dev(user):
    """El rol de desarrollo ve y puede tocar todos los eventos."""
    return user.is_superuser or user.rol == Rol.ADMIN


def cursos_publicables(user):
    """Cursos para los que esta persona puede dirigir un evento."""
    if es_direccion(user):
        return Curso.objects.all()
    if user.rol == Rol.DOCENTE:
        return Curso.objects.filter(plan__asignaciones__docente=user).distinct()
    if user.rol == Rol.PRECEPTOR:
        return Curso.objects.filter(preceptores__preceptor=user)
    return Curso.objects.none()


def roles_de_curso_permitidos(user):
    """A qué integrantes de un curso puede dirigirse esta persona."""
    if es_direccion(user):
        return ROLES_DE_CURSO
    if user.rol == Rol.DOCENTE:
        return (Rol.ALUMNO, Rol.FAMILIA, Rol.PRECEPTOR)
    if user.rol == Rol.PRECEPTOR:
        return (Rol.ALUMNO, Rol.FAMILIA, Rol.DOCENTE)
    return ()


def roles_de_curso_por_defecto(user):
    """Lo que viene tildado al abrir el formulario."""
    if user.rol == Rol.DOCENTE:
        return (Rol.ALUMNO, Rol.FAMILIA, Rol.PRECEPTOR)
    if user.rol == Rol.PRECEPTOR:
        return (Rol.ALUMNO, Rol.FAMILIA)
    return ()


def filtro_visibilidad(user):
    """Condición para los eventos que esta persona puede ver."""
    q = (
        Q(creado_por=user)
        | Q(destinos__tipo=T.TODOS)
        | Q(destinos__tipo=T.ROL, destinos__rol=user.rol)
    )
    if user.rol == Rol.ALUMNO:
        cursos = Inscripcion.objects.filter(alumno=user).values('curso')
    elif user.rol == Rol.FAMILIA:
        hijos = VinculoFamiliar.objects.filter(tutor=user).values('alumno')
        cursos = Inscripcion.objects.filter(alumno__in=hijos).values('curso')
    elif user.rol == Rol.DOCENTE:
        cursos = MateriaCurso.objects.filter(asignaciones__docente=user).values('curso')
    elif user.rol == Rol.PRECEPTOR:
        cursos = AsignacionPreceptor.objects.filter(preceptor=user).values('curso')
    else:
        return q
    return q | Q(destinos__tipo=T.CURSO, destinos__rol=user.rol, destinos__curso__in=cursos)


def usuarios_de_destino(tipo, rol, curso):
    """Personas que ven un evento por este destino (para el recuento previo a publicar)."""
    base = Usuario.objects.filter(is_active=True).exclude(is_superuser=True)
    if tipo == T.TODOS:
        return base
    if tipo == T.ROL:
        return base.filter(rol=rol)
    if tipo == T.CURSO:
        if rol == Rol.ALUMNO:
            return base.filter(inscripciones__curso=curso).distinct()
        if rol == Rol.FAMILIA:
            return base.filter(alumnos_a_cargo__alumno__inscripciones__curso=curso).distinct()
        if rol == Rol.DOCENTE:
            return base.filter(asignaciones__materia_curso__curso=curso).distinct()
        if rol == Rol.PRECEPTOR:
            return base.filter(cursos_a_cargo__curso=curso).distinct()
    return base.none()


def texto_destino(tipo, rol, curso):
    if tipo == T.TODOS:
        return 'Toda la escuela'
    if tipo == T.ROL:
        return PLURAL.get(rol, rol)
    if tipo == T.CURSO:
        return f"{PLURAL.get(rol, rol)} de {curso.nombre if curso else '?'}"
    return ''