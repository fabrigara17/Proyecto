from rest_framework import serializers
from .models import Comunicacion


class ComunicacionSerializer(serializers.ModelSerializer):
    autor = serializers.SerializerMethodField()
    # Solo viene en el listado de quien lee (lo calcula el queryset); en otras respuestas se omite
    visto = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comunicacion
        fields = ['id', 'titulo', 'contenido', 'autor', 'tipo', 'fecha_publicacion', 'visto']
        read_only_fields = ['id', 'fecha_publicacion']

    def get_autor(self, obj):
        if obj.autor is None:
            return None
        return obj.autor.get_full_name() or obj.autor.username


class ComunicacionAdminSerializer(ComunicacionSerializer):
    cant_vistas = serializers.IntegerField(read_only=True)
    total_destinatarios = serializers.SerializerMethodField()

    class Meta(ComunicacionSerializer.Meta):
        fields = ComunicacionSerializer.Meta.fields + ['cant_vistas', 'total_destinatarios']

    def get_total_destinatarios(self, obj):
        return self.context.get('total_destinatarios')