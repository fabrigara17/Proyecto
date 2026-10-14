from django.utils import timezone
from rest_framework import serializers

from academico.models import Inscripcion, MateriaCurso, AsignacionDocente
from users.models import Rol
from .models import Calificacion, Etapa


class EtapaSerializer(serializers.ModelSerializer):
    esta_abierta = serializers.BooleanField(read_only=True)

    class Meta:
        model = Etapa
        fields = ['id', 'nombre', 'anio_lectivo', 'fecha_inicio', 'fecha_fin', 'habilitada', 'esta_abierta']
        read_only_fields = ['id']

    def validate(self, attrs):
        g = lambda k: attrs.get(k, getattr(self.instance, k, None))
        if g('fecha_fin') < g('fecha_inicio'):
            raise serializers.ValidationError('La fecha de fin no puede ser anterior a la de inicio.')
        return attrs


class CalificacionSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    etapa_nombre = serializers.SerializerMethodField()
    etapa_abierta = serializers.SerializerMethodField()

    class Meta:
        model = Calificacion
        fields = [
            'id', 'alumno', 'alumno_nombre', 'materia', 'materia_nombre',
            'curso', 'curso_nombre', 'etapa', 'etapa_nombre', 'etapa_abierta',
            'nota', 'detalle', 'fecha', 'docente',
        ]
        read_only_fields = ['id', 'docente']
        extra_kwargs = {'fecha': {'required': False}}  # si no viene, se usa la de hoy

    def get_alumno_nombre(self, obj):
        return obj.alumno.get_full_name() or obj.alumno.username

    def get_etapa_nombre(self, obj):
        return obj.etapa.nombre if obj.etapa_id else None

    def get_etapa_abierta(self, obj):
        return obj.etapa.esta_abierta if obj.etapa_id else False

    def validate(self, attrs):
        g = lambda k: attrs.get(k, getattr(self.instance, k, None))
        alumno, materia, curso, etapa = g('alumno'), g('materia'), g('curso'), g('etapa')
        user = self.context['request'].user

        if not Inscripcion.objects.filter(alumno=alumno, curso=curso).exists():
            raise serializers.ValidationError('El alumno no está inscripto en ese curso.')

        if not MateriaCurso.objects.filter(curso=curso, materia=materia).exists():
            raise serializers.ValidationError('Esa materia no pertenece al plan de ese curso.')

        if user.rol == Rol.DOCENTE and not user.is_superuser:
            if not AsignacionDocente.objects.filter(
                docente=user, materia_curso__materia=materia, materia_curso__curso=curso,
            ).exists():
                raise serializers.ValidationError('No tenés asignada esa materia en ese curso.')

        # Etapa: obligatoria, del mismo año lectivo que el curso y habilitada por conducción
        if etapa is None:
            raise serializers.ValidationError({'etapa': 'Elegí la etapa de la nota.'})
        if etapa.anio_lectivo != curso.anio_lectivo:
            raise serializers.ValidationError({'etapa': 'La etapa no corresponde al año lectivo del curso.'})
        if not user.is_superuser:
            # Al editar también cuenta la etapa en la que la nota estaba cargada
            etapas = {etapa}
            if self.instance is not None and self.instance.etapa_id:
                etapas.add(self.instance.etapa)
            for e in etapas:
                if not e.esta_abierta:
                    raise serializers.ValidationError({
                        'etapa': f'La etapa "{e.nombre}" no está habilitada para cargar o modificar notas.'
                    })

        if self.instance is None:
            attrs.setdefault('fecha', timezone.localdate())
        return attrs