from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import EstaAutenticado
from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionesViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [EstaAutenticado]
    # 'post' es necesario para la acción marcar-todas-leidas. No hay CreateModelMixin,
    # así que POST sobre la lista sigue sin existir (405). PUT queda excluido a propósito.
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).order_by('-fecha_creacion')

    @action(detail=False, methods=['get'], url_path='no-leidas')
    def no_leidas(self, request):
        return Response({'cantidad': self.get_queryset().filter(leida=False).count()})

    @action(detail=False, methods=['post'], url_path='marcar-todas-leidas')
    def marcar_todas_leidas(self, request):
        n = self.get_queryset().filter(leida=False).update(leida=True)
        return Response({'actualizadas': n})