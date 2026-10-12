from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'mensaje', 'leida', 'fecha_creacion', 'tipo', 'referencia_id']
        read_only_fields = ['id', 'mensaje', 'fecha_creacion', 'tipo', 'referencia_id']