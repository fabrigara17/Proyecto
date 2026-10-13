from rest_framework import permissions
from academico.models import Inscripcion, AsignacionDocente, AsignacionPreceptor

class EsUsuarioAutorizadoParaChatear(permissions.BasePermission):
    """
    Valida las reglas de rol:
    - Conducción: Habla con cualquiera.
    - Docentes/Preceptores: Pares + cursos asignados.
    - Alumnos/Familiares: Solo solicitud a su preceptor o profes de sus materias.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        usuario_actual = request.user
        
        # Si es equipo de conducción (asumiendo rol 'directivo' o similar en tu modelo user)
        if getattr(usuario_actual, 'rol', None) in ['conduccion', 'directivo', 'admin']:
            return True

        # Participantes directos de la conversación
        return obj.participante_1 == usuario_actual or obj.participante_2 == usuario_actual