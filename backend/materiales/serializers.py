import os

from rest_framework import serializers
from rest_framework.reverse import reverse
from academico.models import AsignacionDocente
from users.models import Rol
from .models import Consulta, Material

EXTENSIONES_PERMITIDAS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.txt',
}
MAX_MB = 10


class MaterialSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia_curso.materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='materia_curso.curso.nombre', read_only=True)
    docente_nombre = serializers.SerializerMethodField()
    archivo_url = serializers.SerializerMethodField()
    archivo_nombre = serializers.SerializerMethodField()
    consultas_count = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'titulo', 'descripcion', 'archivo', 'archivo_url', 'archivo_nombre',
            'materia_curso', 'materia_nombre', 'curso_nombre',
            'docente_nombre', 'fecha_subida', 'consultas_count',
        ]
        read_only_fields = ['id', 'fecha_subida']
        extra_kwargs = {'archivo': {'write_only': True}}

    def get_docente_nombre(self, obj):
        if obj.docente is None:
            return None
        return obj.docente.get_full_name() or obj.docente.username

    def get_archivo_url(self, obj):
        return reverse('material-descargar', args=[obj.pk], request=self.context.get('request'))

    def get_archivo_nombre(self, obj):
        return os.path.basename(obj.archivo.name)

    def get_consultas_count(self, obj):
        # En los listados viene anotado; al crear un material todavía no
        n = getattr(obj, 'consultas_count', None)
        return n if n is not None else obj.consultas.count()

    def validate_archivo(self, f):
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in EXTENSIONES_PERMITIDAS:
            raise serializers.ValidationError(
                'Tipo de archivo no permitido. Podés subir: '
                + ', '.join(sorted(e.lstrip('.') for e in EXTENSIONES_PERMITIDAS)) + '.'
            )
        if f.size > MAX_MB * 1024 * 1024:
            raise serializers.ValidationError(f'El archivo supera los {MAX_MB} MB.')
        return f

    def validate_materia_curso(self, materia_curso):
        user = self.context['request'].user
        if user.rol == Rol.DOCENTE and not user.is_superuser:
            if not AsignacionDocente.objects.filter(
                docente=user, materia_curso=materia_curso,
            ).exists():
                raise serializers.ValidationError('No tenés asignada esa materia en ese curso.')
        return materia_curso


class ConsultaSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.SerializerMethodField()
    autor_rol = serializers.SerializerMethodField()
    es_mio = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = ['id', 'autor_nombre', 'autor_rol', 'es_mio', 'texto', 'fecha']
        read_only_fields = ['id', 'fecha']

    def get_autor_nombre(self, obj):
        if obj.autor is None:
            return 'Usuario eliminado'
        return obj.autor.get_full_name() or obj.autor.username

    def get_autor_rol(self, obj):
        return obj.autor.rol if obj.autor else None

    def get_es_mio(self, obj):
        request = self.context.get('request')
        return bool(request and obj.autor_id == request.user.id)