from django.db import transaction
from rest_framework import serializers

from .models import DestinoEvento, Evento
from .servicios import (
    ROLES_DE_CATEGORIA, cursos_publicables, es_dev, es_direccion,
    roles_de_curso_permitidos, texto_destino,
)

T = DestinoEvento.Tipo


def limpiar_destinos(user, destinos):
    """Valida cada destino contra lo que este usuario puede elegir y quita repetidos."""
    vistos, limpios = set(), []
    for original in destinos:
        d = dict(original)
        tipo, rol, curso = d.get('tipo'), d.get('rol') or '', d.get('curso')

        if tipo == T.TODOS:
            if not es_direccion(user):
                raise serializers.ValidationError('Solo la conducción puede dirigirse a toda la escuela.')
            d['rol'], d['curso'] = '', None
        elif tipo == T.ROL:
            if not es_direccion(user):
                raise serializers.ValidationError('Solo la conducción puede elegir una categoría completa.')
            if rol not in ROLES_DE_CATEGORIA:
                raise serializers.ValidationError('Elegí una categoría válida.')
            d['curso'] = None
        elif tipo == T.CURSO:
            if curso is None:
                raise serializers.ValidationError('Elegí un curso.')
            if rol not in roles_de_curso_permitidos(user):
                raise serializers.ValidationError('No podés dirigirte a ese grupo.')
            if not cursos_publicables(user).filter(pk=curso.pk).exists():
                raise serializers.ValidationError(f'El curso {curso.nombre} no está a tu cargo.')
        else:
            raise serializers.ValidationError('Destino no válido.')

        clave = (d['tipo'], d.get('rol') or '', d['curso'].pk if d.get('curso') else None)
        if clave not in vistos:
            vistos.add(clave)
            limpios.append(d)
    return limpios


class DestinoSerializer(serializers.ModelSerializer):
    texto = serializers.SerializerMethodField()

    class Meta:
        model = DestinoEvento
        fields = ['tipo', 'rol', 'curso', 'texto']

    def get_texto(self, obj):
        return texto_destino(obj.tipo, obj.rol, obj.curso)


class EventoSerializer(serializers.ModelSerializer):
    destinos = DestinoSerializer(many=True, allow_empty=False)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()
    creado_por_rol = serializers.CharField(source='creado_por.get_rol_display', read_only=True)
    es_mio = serializers.SerializerMethodField()
    puede_editar = serializers.SerializerMethodField()

    class Meta:
        model = Evento
        fields = [
            'id', 'titulo', 'descripcion', 'tipo', 'tipo_display',
            'fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin',
            'destinos', 'creado_por', 'creado_por_nombre', 'creado_por_rol',
            'es_mio', 'puede_editar',
        ]
        read_only_fields = ['id', 'creado_por']
        extra_kwargs = {'fecha_fin': {'required': False}, 'descripcion': {'required': False}}

    def get_creado_por_nombre(self, obj):
        u = obj.creado_por
        return None if u is None else (u.get_full_name() or u.username)

    def get_es_mio(self, obj):
        return obj.creado_por_id == self.context['request'].user.id

    def get_puede_editar(self, obj):
        user = self.context['request'].user
        return obj.creado_por_id == user.id or es_dev(user)

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fin = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None)) or inicio
        if fin < inicio:
            raise serializers.ValidationError('La fecha de fin no puede ser anterior a la de inicio.')
        if (fin - inicio).days > 30:
            raise serializers.ValidationError('Un evento puede durar como máximo 31 días.')
        attrs['fecha_fin'] = fin

        hi = attrs.get('hora_inicio', getattr(self.instance, 'hora_inicio', None))
        hf = attrs.get('hora_fin', getattr(self.instance, 'hora_fin', None))
        if hf and not hi:
            raise serializers.ValidationError('Indicá la hora de inicio.')
        if hi and hf and inicio == fin and hf <= hi:
            raise serializers.ValidationError('La hora de fin tiene que ser posterior a la de inicio.')

        if 'destinos' in attrs:
            attrs['destinos'] = limpiar_destinos(self.context['request'].user, attrs['destinos'])
        return attrs

    def create(self, validated_data):
        destinos = validated_data.pop('destinos')
        with transaction.atomic():
            evento = Evento.objects.create(**validated_data)
            DestinoEvento.objects.bulk_create([DestinoEvento(evento=evento, **d) for d in destinos])
        return evento

    def update(self, instance, validated_data):
        destinos = validated_data.pop('destinos', None)
        with transaction.atomic():
            for campo, valor in validated_data.items():
                setattr(instance, campo, valor)
            instance.save()
            if destinos is not None:
                instance.destinos.all().delete()
                DestinoEvento.objects.bulk_create([DestinoEvento(evento=instance, **d) for d in destinos])
        return instance


class DestinosPreviewSerializer(serializers.Serializer):
    destinos = DestinoSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        attrs['destinos'] = limpiar_destinos(self.context['request'].user, attrs['destinos'])
        return attrs