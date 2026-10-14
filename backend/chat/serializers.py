import os

from rest_framework import serializers
from .models import Conversacion, Mensaje
from users.serializers import UsuarioSerializer

EXTENSIONES_PERMITIDAS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.txt',
}
MAX_MB = 10


class MensajeSerializer(serializers.ModelSerializer):
    remisor_nombre = serializers.CharField(source='remisor.get_full_name', read_only=True)
    archivo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Mensaje
        fields = ['id', 'conversacion', 'remisor', 'remisor_nombre', 'texto',
                  'archivo', 'archivo_nombre', 'leido', 'fecha_envio']
        read_only_fields = ['remisor', 'leido']
        extra_kwargs = {
            'texto': {'required': False, 'allow_blank': True},
            'archivo': {'write_only': True, 'required': False},
        }

    def get_archivo_nombre(self, obj):
        return os.path.basename(obj.archivo.name) if obj.archivo else None

    def validate_archivo(self, f):
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in EXTENSIONES_PERMITIDAS:
            raise serializers.ValidationError(
                'Tipo de archivo no permitido. Podés enviar: '
                + ', '.join(sorted(e.lstrip('.') for e in EXTENSIONES_PERMITIDAS)) + '.'
            )
        if f.size > MAX_MB * 1024 * 1024:
            raise serializers.ValidationError(f'El archivo supera los {MAX_MB} MB.')
        return f

    def validate(self, attrs):
        texto = (attrs.get('texto') or '').strip()
        if not texto and not attrs.get('archivo'):
            raise serializers.ValidationError('Escribí un mensaje o adjuntá un archivo.')
        return attrs


class ConversacionSerializer(serializers.ModelSerializer):
    participante_1_detalles = UsuarioSerializer(source='participante_1', read_only=True)
    participante_2_detalles = UsuarioSerializer(source='participante_2', read_only=True)
    ultimo_mensaje = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = ['id', 'participante_1', 'participante_2', 'participante_1_detalles', 'participante_2_detalles', 'estado', 'iniciado_por', 'fecha_creacion', 'ultimo_mensaje']
        read_only_fields = ['participante_1', 'estado', 'iniciado_por']

    def get_ultimo_mensaje(self, obj):
        ultimo = obj.mensajes.order_by('-fecha_envio').first()
        if ultimo:
            return MensajeSerializer(ultimo).data
        return None