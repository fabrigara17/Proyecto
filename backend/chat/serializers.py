from rest_framework import serializers
from .models import Conversacion, Mensaje
from users.serializers import UsuarioSerializer # Asumiendo que existe un serializador de usuario

class MensajeSerializer(serializers.ModelSerializer):
    remisor_nombre = serializers.CharField(source='remisor.get_full_name', read_only=True)

    class Meta:
        model = Mensaje
        fields = ['id', 'conversacion', 'remisor', 'remisor_nombre', 'texto', 'leido', 'fecha_envio']
        read_only_fields = ['remisor', 'leido']

class ConversacionSerializer(serializers.ModelSerializer):
    participante_1_detalles = UsuarioSerializer(source='participante_1', read_only=True)
    participante_2_detalles = UsuarioSerializer(source='participante_2', read_only=True)
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = ['id', 'participante_1', 'participante_2', 'participante_1_detalles', 'participante_2_detalles', 'estado', 'iniciado_por', 'fecha_creacion', 'ultimo_mensaje']
        read_only_fields = ['estado', 'iniciado_por']

    def get_ultimo_mensaje(self, obj):
        ultimo = obj.mensajes.order_by('-fecha_envio').first()
        if ultimo:
            return MensajeSerializer(ultimo).data
        return None