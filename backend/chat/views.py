from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db.models import Q
from .models import Conversacion, Mensaje
from .serializers import ConversacionSerializer, MensajeSerializer
from .permissions import EsUsuarioAutorizadoParaChatear
from rest_framework.decorators import action
from users.models import Usuario
from users.serializers import UsuarioSerializer
from academico.models import Curso, Inscripcion, AsignacionPreceptor, AsignacionDocente

class ConversacionViewSet(viewsets.ModelViewSet):
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated, EsUsuarioAutorizadoParaChatear]

    def get_queryset(self,):
        usuario = self.request.user
        # Devuelve solo las conversaciones donde el usuario actual participa
        return Conversacion.objects.filter(Q(participante_1=usuario) | Q(participante_2=usuario)).order_by('-actualizado_en')

    def perform_create(self, serializer):
        remisor = self.request.user
        destinatario = serializer.validated_data.get('participante_2')
        
        # Regla para Alumnos y Familiares: Inician como 'pendiente' (solicitud)
        estado_inicial = 'aceptada'
        if remisor.rol in ['alumno', 'familiar']:
            estado_inicial = 'pendiente'
            # Validar si el destinatario es su profesor o preceptor asignado (puedes agregar tu validación aquí)

        serializer.save(
            participante_1=remisor,
            iniciado_por=remisor,
            estado=estado_inicial
        )

    @action(detail=False, methods=['get'])
    def usuarios_disponibles(self, request):
        usuario_actual = request.user
        rol = getattr(usuario_actual, 'rol', None)
        
        # 1. Conducción ve a todos
        if rol in ['conduccion', 'directivo', 'ADMIN']:
            usuarios = Usuario.objects.exclude(id=usuario_actual.id)
            return Response(UsuarioSerializer(usuarios, many=True).data)

        # 2. Preceptores / Docentes: ven a otros docentes, preceptores, conducción, y a los alumnos/familias de sus cursos
        if rol in ['PRECEPTOR', 'docente', 'preceptor']:
            # Pares institucionales
            pares = Usuario.objects.filter(rol__in=['CONDUCCION', 'PRECEPTOR', 'docente', 'DIRECTIVO', 'ADMIN']).exclude(id=usuario_actual.id)
            
            # Alumnos de sus cursos asignados (si es preceptor o docente)
            cursos_ids = []
            if rol.upper() == 'PRECEPTOR' or rol == 'preceptor':
                cursos_ids = AsignacionPreceptor.objects.filter(preceptor=usuario_actual).values_list('curso_id', flat=True)
            else:
                cursos_ids = AsignacionDocente.objects.filter(docente=usuario_actual).values_list('curso_id', flat=True)
                
            inscripciones = Inscripcion.objects.filter(curso_id__in=cursos_ids)
            alumnos_ids = inscripciones.values_list('alumno_id', flat=True)
            
            # Unimos los usuarios permitidos
            usuarios_permitidos = (pares | Usuario.objects.filter(id__in=alumnos_ids)).distinct().exclude(id=usuario_actual.id)
            return Response(UsuarioSerializer(usuarios_permitidos, many=True).data)

        # 3. Alumnos y Familiares: solo pueden ver a sus preceptores y profesores
        # (Aquí puedes ajustar según tu lógica de familia/alumno)
        return Response([])

    @action(detail=False, methods=['get'])
    def usuarios_disponibles(self, request):
        usuario_actual = request.user
        if not usuario_actual.is_authenticated:
            return Response([])

        rol_actual = str(getattr(usuario_actual, 'rol', '')).upper()
        
        # Alumnos y familiares no pueden iniciar chats directos
        if rol_actual in ['ALUMNO', 'FAMILIAR']:
            return Response([])

        filtro_rol = request.query_params.get('rol', 'todos').lower()

        # Obtener todos los usuarios salvo el actual
        qs = Usuario.objects.exclude(id=usuario_actual.id)

        # Si se selecciona un filtro de rol específico
        if filtro_rol == 'conduccion':
            qs = qs.filter(rol__icontains='CONDUCCION') | qs.filter(rol__icontains='DIRECTIVO') | qs.filter(rol__icontains='ADMIN')
        elif filtro_rol == 'preceptor':
            qs = qs.filter(rol__icontains='PRECEPTOR')
        elif filtro_rol == 'docente':
            qs = qs.filter(rol__icontains='DOCENTE') or qs.filter(rol__icontains='PROFESOR')
        elif filtro_rol == 'alumno':
            # Si es preceptor, buscar los alumnos de sus cursos
            if 'PRECEPTOR' in rol_actual:
                cursos_ids = AsignacionPreceptor.objects.filter(preceptor=usuario_actual).values_list('curso_id', flat=True)
                alumnos_ids = Inscripcion.objects.filter(curso_id__in=cursos_ids).values_list('alumno_id', flat=True)
                qs = Usuario.objects.filter(id__in=alumnos_ids).exclude(id=usuario_actual.id)
            else:
                qs = qs.filter(rol__in=['ALUMNO', 'FAMILIAR', 'alumno', 'familiar'])

        return Response(UsuarioSerializer(qs.distinct(), many=True).data)

class MensajeViewSet(viewsets.ModelViewSet):
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversacion_id = self.request.query_params.get('conversacion')
        if conversacion_id:
            return Mensaje.objects.filter(conversacion_id=conversacion_id).order_by('fecha_envio')
        return Mensaje.objects.none()

    def perform_create(self, serializer):
        conversacion = serializer.validated_data.get('conversacion')
        usuario = self.request.user
        
        # Validar que el usuario pertenezca a la conversación
        if conversacion.participante_1 != usuario and conversacion.participante_2 != usuario:
            raise PermissionDenied("No puedes enviar mensajes en una conversación ajena.")
            
        serializer.save(remisor=usuario)