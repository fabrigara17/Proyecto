import os

from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Conversacion, Mensaje
from .serializers import ConversacionSerializer, MensajeSerializer
from .permissions import EsUsuarioAutorizadoParaChatear
from users.models import Usuario, Rol
from users.serializers import UsuarioSerializer
from academico.models import Curso, Inscripcion, AsignacionPreceptor, AsignacionDocente, VinculoFamiliar

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
        if remisor.rol in (Rol.ALUMNO, Rol.FAMILIA):
            estado_inicial = 'pendiente'
            # Validar si el destinatario es su profesor o preceptor asignado (puedes agregar tu validación aquí)

        serializer.save(
            participante_1=remisor,
            iniciado_por=remisor,
            estado=estado_inicial
        )

    @action(detail=False, methods=['get'], pagination_class=None)
    def usuarios_disponibles(self, request):
        """Usuarios con los que el usuario actual puede iniciar una conversación.
        Filtro opcional: ?rol=todos|conduccion|preceptor|docente|alumno
        """
        usuario_actual = request.user

        # Alumnos y familias no pueden iniciar chats directos
        if usuario_actual.rol in (Rol.ALUMNO, Rol.FAMILIA):
            return Response([])

        filtro_rol = request.query_params.get('rol', 'todos').lower()
        qs = Usuario.objects.filter(is_active=True).exclude(id=usuario_actual.id)

        if filtro_rol == 'conduccion':
            qs = qs.filter(rol__in=[Rol.CONDUCCION, Rol.ADMIN])
        elif filtro_rol == 'preceptor':
            qs = qs.filter(rol=Rol.PRECEPTOR)
        elif filtro_rol == 'docente':
            qs = qs.filter(rol=Rol.DOCENTE)
        elif filtro_rol == 'alumno':
            if usuario_actual.rol == Rol.PRECEPTOR:
                # Preceptor: alumnos de sus cursos + las familias (tutores) de esos alumnos
                cursos_ids = AsignacionPreceptor.objects.filter(
                    preceptor=usuario_actual).values_list('curso_id', flat=True)
                alumnos_ids = list(Inscripcion.objects.filter(
                    curso_id__in=cursos_ids).values_list('alumno_id', flat=True))
                tutores_ids = list(VinculoFamiliar.objects.filter(
                    alumno_id__in=alumnos_ids).values_list('tutor_id', flat=True))
                qs = qs.filter(id__in=alumnos_ids + tutores_ids)
            else:
                qs = qs.filter(rol__in=[Rol.ALUMNO, Rol.FAMILIA])

        qs = qs.order_by('last_name', 'first_name', 'username')
        return Response(UsuarioSerializer(qs, many=True).data)

class MensajeViewSet(viewsets.ModelViewSet):
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # Sin PUT/PATCH/DELETE: nadie puede editar ni borrar mensajes (ni adjuntos) ajenos
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        usuario = self.request.user
        # Solo mensajes de conversaciones en las que el usuario participa
        qs = Mensaje.objects.filter(
            Q(conversacion__participante_1=usuario) | Q(conversacion__participante_2=usuario)
        )
        if self.action == 'list':
            conversacion_id = self.request.query_params.get('conversacion')
            if not conversacion_id:
                return Mensaje.objects.none()
            qs = qs.filter(conversacion_id=conversacion_id)
        return qs.order_by('fecha_envio')

    def perform_create(self, serializer):
        conversacion = serializer.validated_data.get('conversacion')
        usuario = self.request.user
        
        # Validar que el usuario pertenezca a la conversación
        if conversacion.participante_1 != usuario and conversacion.participante_2 != usuario:
            raise PermissionDenied("No puedes enviar mensajes en una conversación ajena.")
            
        serializer.save(remisor=usuario)

    @action(detail=True, methods=['get'], url_path='descargar')
    def descargar(self, request, pk=None):
        mensaje = self.get_object()  # 404 si el usuario no participa de la conversación
        if not mensaje.archivo:
            raise Http404('Este mensaje no tiene archivo.')
        try:
            archivo = mensaje.archivo.open('rb')
        except FileNotFoundError:
            raise Http404('El archivo ya no está disponible.')
        return FileResponse(
            archivo, as_attachment=True, filename=os.path.basename(mensaje.archivo.name),
        )