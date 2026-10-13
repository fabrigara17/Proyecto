from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from academico.views import (
    CursoViewSet, MateriaViewSet, MateriaCursoViewSet, InscripcionViewSet,
    AsignacionDocenteViewSet, VinculoFamiliarViewSet, AsignacionPreceptorViewSet
)
from asistencias.views import AsistenciaViewSet, DiaSinClasesViewSet
from calificaciones.views import CalificacionesViewSet
from comunicaciones.views import ComunicacionViewSet
from materiales.views import MaterialViewSet
from notificaciones.views import NotificacionesViewSet
from users.views import LoginView, UsuarioViewSet, perfil, cambiar_password, logout
from calendario.views import EventoViewSet

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet, basename='usuario')
router.register('cursos', CursoViewSet, basename='curso')
router.register('materias', MateriaViewSet, basename='materia')
router.register('plan-estudios', MateriaCursoViewSet, basename='materia-curso')
router.register('inscripciones', InscripcionViewSet, basename='inscripcion')
router.register('asignaciones', AsignacionDocenteViewSet, basename='asignacion')
router.register('vinculos-familiares', VinculoFamiliarViewSet, basename='vinculo-familiar')
router.register('asistencias', AsistenciaViewSet, basename='asistencia')
router.register('calificaciones', CalificacionesViewSet, basename='calificacion')
router.register('comunicaciones', ComunicacionViewSet, basename='comunicacion')
router.register('notificaciones', NotificacionesViewSet, basename='notificacion')
router.register('materiales', MaterialViewSet, basename='material')
router.register('asignaciones-preceptor', AsignacionPreceptorViewSet, basename='asignacion-preceptor')
router.register('dias-sin-clases', DiaSinClasesViewSet, basename='dia-sin-clases')
router.register('eventos', EventoViewSet, basename='evento')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/auth/perfil/', perfil, name='perfil'),
    path('api/auth/cambiar-password/', cambiar_password, name='cambiar_password'),
]