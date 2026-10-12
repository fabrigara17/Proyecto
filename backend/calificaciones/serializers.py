from rest_framework import serializers

from academico.models import Inscripcion, MateriaCurso, AsignacionDocente
from users.models import Rol
from .models import Calificacion


class CalificacionSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)

    class Meta:
        model = Calificacion
        fields = [
            'id', 'alumno', 'alumno_nombre', 'materia', 'materia_nombre',
            'curso', 'curso_nombre', 'nota', 'fecha', 'docente',
        ]
        read_only_fields = ['id', 'docente']

    def get_alumno_nombre(self, obj):
        return obj.alumno.get_full_name() or obj.alumno.username

    def validate(self, attrs):
        g = lambda k: attrs.get(k, getattr(self.instance, k, None))
        alumno, materia, curso = g('alumno'), g('materia'), g('curso')
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
        return attrs