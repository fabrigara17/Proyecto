import os

from django.http import FileResponse, Http404
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from academico.models import Inscripcion, VinculoFamiliar
from notificaciones.models import Notificacion
from users.models import Rol
from users.permissions import EsDocenteOAdmin, EstaAutenticado
from .models import Material
from .serializers import ConsultaSerializer, MaterialSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [EsDocenteOAdmin()]
        return [EstaAutenticado()]

    def get_queryset(self):
        user = self.request.user
        qs = Material.objects.select_related(
            'materia_curso__materia', 'materia_curso__curso', 'docente',
        ).annotate(consultas_count=Count('consultas', distinct=True))

        if user.is_superuser or user.rol in (Rol.ADMIN, Rol.PRECEPTOR):
            return qs
        if user.rol == Rol.DOCENTE:
            return qs.filter(docente=user)
        if user.rol == Rol.ALUMNO:
            return qs.filter(materia_curso__curso__inscripciones__alumno=user).distinct()
        if user.rol == Rol.FAMILIA:
            alumnos = VinculoFamiliar.objects.filter(tutor=user).values('alumno')
            return qs.filter(materia_curso__curso__inscripciones__alumno__in=alumnos).distinct()
        return qs.none()

    def perform_create(self, serializer):
        material = serializer.save(docente=self.request.user)
        mc = material.materia_curso

        # Avisamos a los alumnos del curso y a sus familias
        alumnos_ids = list(
            Inscripcion.objects.filter(curso=mc.curso).values_list('alumno_id', flat=True)
        )
        tutores_ids = VinculoFamiliar.objects.filter(
            alumno_id__in=alumnos_ids
        ).values_list('tutor_id', flat=True)
        destinatarios = set(alumnos_ids) | set(tutores_ids)

        mensaje = f"Nuevo material en {mc.materia}: {material.titulo}"[:255]
        Notificacion.objects.bulk_create([
            Notificacion(
                usuario_id=uid, mensaje=mensaje,
                tipo=Notificacion.Tipo.MATERIAL, referencia_id=material.id,
            )
            for uid in destinatarios
        ])

    def perform_destroy(self, instance):
        instance.archivo.delete(save=False)  # borra también el archivo del disco
        instance.delete()

    @action(detail=True, methods=['get'], url_path='descargar')
    def descargar(self, request, pk=None):
        material = self.get_object()  # 404 si el usuario no tiene acceso a este material
        try:
            archivo = material.archivo.open('rb')
        except FileNotFoundError:
            raise Http404('El archivo ya no está disponible.')
        return FileResponse(
            archivo, as_attachment=True, filename=os.path.basename(material.archivo.name),
        )

    @action(detail=True, methods=['get', 'post'], url_path='consultas', parser_classes=[JSONParser])
    def consultas(self, request, pk=None):
        # get_object() usa get_queryset(): si no tiene acceso al material, da 404
        material = self.get_object()
        contexto = {'request': request}

        if request.method == 'GET':
            qs = material.consultas.select_related('autor')
            return Response(ConsultaSerializer(qs, many=True, context=contexto).data)

        serializer = ConsultaSerializer(data=request.data, context=contexto)
        serializer.is_valid(raise_exception=True)
        consulta = serializer.save(material=material, autor=request.user)
        self._notificar_consulta(material, consulta)
        return Response(ConsultaSerializer(consulta, context=contexto).data, status=201)

    def _notificar_consulta(self, material, consulta):
        autor = consulta.autor
        nombre = autor.get_full_name() or autor.username

        if autor.id == material.docente_id:
            # Respondió el docente: avisamos a quienes ya participaron en el hilo
            destinatarios = set(
                material.consultas.exclude(autor=autor).values_list('autor_id', flat=True)
            )
            mensaje = f'{nombre} respondió en "{material.titulo}"'
        else:
            destinatarios = {material.docente_id}
            mensaje = f'Nueva consulta de {nombre} en "{material.titulo}"'

        destinatarios.discard(None)
        destinatarios.discard(autor.id)
        Notificacion.objects.bulk_create([
            Notificacion(
                usuario_id=uid, mensaje=mensaje[:255],
                tipo=Notificacion.Tipo.CONSULTA, referencia_id=material.id,
            )
            for uid in destinatarios
        ])