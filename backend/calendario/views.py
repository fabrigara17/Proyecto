from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.utils.dateparse import parse_date

from users.models import Rol
from users.permissions import EstaAutenticado, PuedeEditarCalendario
from .models import Evento
from .serializers import DestinosPreviewSerializer, EventoSerializer
from .servicios import (
    PLURAL, ROLES_DE_CATEGORIA, cursos_publicables, es_dev, es_direccion, filtro_visibilidad,
    roles_de_curso_permitidos, roles_de_curso_por_defecto, texto_destino, usuarios_de_destino,
)


def _fecha(valor, nombre):
    try:
        f = parse_date(valor or '')
    except ValueError:
        f = None
    if f is None:
        raise ValidationError({nombre: 'Indicá la fecha en formato YYYY-MM-DD.'})
    return f


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    pagination_class = None  # el calendario pide un rango de fechas y recibe una lista

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [EstaAutenticado()]
        return [PuedeEditarCalendario()]

    def get_queryset(self):
        user = self.request.user
        qs = Evento.objects.select_related('creado_por').prefetch_related('destinos__curso')

        # Editar o borrar: solo lo propio (el rol de desarrollo puede todo)
        if self.action in ('update', 'partial_update', 'destroy'):
            return qs if es_dev(user) else qs.filter(creado_por=user)

        if not es_dev(user):
            qs = qs.filter(filtro_visibilidad(user)).distinct()

        if self.action == 'list':
            desde = _fecha(self.request.query_params.get('desde'), 'desde')
            hasta = _fecha(self.request.query_params.get('hasta'), 'hasta')
            if hasta < desde or (hasta - desde).days > 100:
                raise ValidationError('El rango de fechas no es válido.')
            qs = qs.filter(fecha_inicio__lte=hasta, fecha_fin__gte=desde)
        return qs

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def opciones(self, request):
        """Lo que esta persona puede elegir como destinatarios."""
        user = request.user
        direccion = es_direccion(user)
        por_defecto = roles_de_curso_por_defecto(user)
        return Response({
            'toda_escuela': direccion,
            'categorias': (
                [{'valor': r, 'texto': PLURAL[r]} for r in ROLES_DE_CATEGORIA] if direccion else []
            ),
            'cursos': [
                {'id': c.id, 'nombre': c.nombre, 'anio_lectivo': c.anio_lectivo}
                for c in cursos_publicables(user).order_by('-anio_lectivo', 'nombre')
            ],
            'roles_curso': [
                {'valor': r, 'texto': PLURAL[r], 'marcado': r in por_defecto}
                for r in roles_de_curso_permitidos(user)
            ],
        })

    @action(detail=False, methods=['post'])
    def destinatarios(self, request):
        """Cuántas personas lo van a ver con estos destinos (antes de publicar)."""
        serializer = DestinosPreviewSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ids, detalle = set(), []
        for d in serializer.validated_data['destinos']:
            usuarios = list(
                usuarios_de_destino(d['tipo'], d.get('rol') or '', d.get('curso')).values_list('id', flat=True)
            )
            ids.update(usuarios)
            detalle.append({
                'texto': texto_destino(d['tipo'], d.get('rol') or '', d.get('curso')),
                'cantidad': len(usuarios),
            })
        return Response({'total': len(ids), 'detalle': detalle})