from rest_framework import serializers
from users.models import Usuario
from django.db import transaction
from .models import (
    Curso, Materia, MateriaCurso, Inscripcion, AsignacionDocente,
    AsignacionPreceptor, VinculoFamiliar,
)


class CursoSerializer(serializers.ModelSerializer):
    # Los contadores los calcula el listado; en las demás respuestas se omiten
    cant_alumnos = serializers.IntegerField(read_only=True)
    cant_materias = serializers.IntegerField(read_only=True)
    # Al crear el curso se pueden indicar todas sus materias de una vez
    materias = serializers.PrimaryKeyRelatedField(
        queryset=Materia.objects.all(), many=True, write_only=True, required=False,
    )

    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'anio_cursada', 'anio_lectivo', 'cant_alumnos', 'cant_materias', 'materias']

    def create(self, validated_data):
        materias = validated_data.pop('materias', [])
        sin_repetir = {m.pk: m for m in materias}.values()
        with transaction.atomic():
            curso = super().create(validated_data)
            MateriaCurso.objects.bulk_create([MateriaCurso(curso=curso, materia=m) for m in sin_repetir])
        return curso

    def update(self, instance, validated_data):
        # Las materias de un curso existente se agregan con la acción "agregar-materias"
        validated_data.pop('materias', None)
        return super().update(instance, validated_data)

class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ['id', 'nombre']


class MateriaCursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MateriaCurso
        fields = ['id', 'curso', 'materia']


class MateriaCursoDetalleSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    anio_lectivo = serializers.IntegerField(source='curso.anio_lectivo', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)

    class Meta:
        model = MateriaCurso
        fields = ['id', 'curso', 'curso_nombre', 'anio_lectivo', 'materia', 'materia_nombre']


class AlumnoSerializer(serializers.ModelSerializer):
    """Datos mínimos de un alumno para listados (sin email)."""
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name']


class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = ['id', 'alumno', 'curso']


class AsignacionDocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionDocente
        fields = ['id', 'docente', 'materia_curso']


class AsignacionPreceptorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionPreceptor
        fields = ['id', 'preceptor', 'curso']


class VinculoFamiliarSerializer(serializers.ModelSerializer):
    class Meta:
        model = VinculoFamiliar
        fields = ['id', 'tutor', 'alumno', 'parentesco']