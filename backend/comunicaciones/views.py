from django.db.models import Count, Exists, OuterRef, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from users.models import ROLES_DIRECCION, Usuario, es_direccion
from users.permissions import EsConduccion, EstaAutenticado
from .models import Comunicacion, ComunicacionVista
from .serializers import ComunicacionAdminSerializer, ComunicacionSerializer


def _destinatarios():
    """A quiénes les llegan los comunicados: usuarios activos que no son de la dirección."""
    return Usuario.objects.filter(is_active=True).exclude(rol__in=ROLES_DIRECCION).exclude(is_superuser=True)


def _nombre(u):
    return u.get_full_name() or u.username


class ComunicacionViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'vistas'):
            return [EsConduccion()]
        return [EstaAutenticado()]

    def get_serializer_class(self):
        return ComunicacionAdminSerializer if es_direccion(self.request.user) else ComunicacionSerializer

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if es_direccion(self.request.user):
            contexto['total_destinatarios'] = _destinatarios().count()
        return contexto

    def get_queryset(self):
        user = self.request.user
        qs = Comunicacion.objects.select_related('autor')
        if es_direccion(user):
            # La dirección solo ve los comunicados que publicó la dirección
            qs = qs.filter(Q(autor__rol__in=ROLES_DIRECCION) | Q(autor__is_superuser=True))
            qs = qs.annotate(cant_vistas=Count('vistas', distinct=True))
        else:
            qs = qs.annotate(visto=Exists(
                ComunicacionVista.objects.filter(comunicacion=OuterRef('pk'), usuario=user)
            ))
        return qs.order_by('-fecha_publicacion')

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @action(detail=False, methods=['post'], url_path='marcar-vistas')
    def marcar_vistas(self, request):
        """Registra que el usuario abrió estos comunicados. La dirección no cuenta como lectora."""
        ids = request.data.get('ids') if isinstance(request.data, dict) else None
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            raise ValidationError({'ids': 'Se esperaba una lista de números.'})
        if es_direccion(request.user):
            return Response(status=204)
        existentes = Comunicacion.objects.filter(id__in=ids[:200]).values_list('id', flat=True)
        ComunicacionVista.objects.bulk_create(
            [ComunicacionVista(comunicacion_id=i, usuario=request.user) for i in existentes],
            ignore_conflicts=True,
        )
        return Response(status=204)

    @action(detail=True, methods=['get'], url_path='vistas')
    def vistas(self, request, pk=None):
        """Quién vio el comunicado y quién todavía no."""
        comunicacion = self.get_object()
        fechas = {v.usuario_id: v.fecha for v in comunicacion.vistas.all()}
        vieron, faltan = [], []
        for u in _destinatarios().order_by('last_name', 'first_name', 'username'):
            item = {'id': u.id, 'nombre': _nombre(u), 'rol_display': u.get_rol_display()}
            if u.id in fechas:
                vieron.append({**item, 'fecha': fechas[u.id]})
            else:
                faltan.append(item)
        vieron.sort(key=lambda x: x['fecha'], reverse=True)
        return Response({'total': len(vieron) + len(faltan), 'vieron': vieron, 'faltan': faltan})