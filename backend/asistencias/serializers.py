from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from academico.models import AsignacionDocente, AsignacionPreceptor, Curso, Inscripcion
from users.models import Rol, Usuario, es_direccion
from .models import Asistencia, DiaSinClases


def validar_acceso_al_curso(user, curso):
    """El docente y el preceptor solo operan sobre los cursos que tienen asignados."""
    if es_direccion(user): 
        return
    if user.rol == Rol.DOCENTE:
        tiene = AsignacionDocente.objects.filter(
            docente=user, materia_curso__curso=curso,
        ).exists()
    elif user.rol == Rol.PRECEPTOR:
        tiene = AsignacionPreceptor.objects.filter(preceptor=user, curso=curso).exists()
    else:
        tiene = False
    if not tiene:
        raise serializers.ValidationError('No tenés asignado ese curso.')


def validar_dia_con_clases(curso, fecha):
    """No se toma asistencia en un día sin clases (del curso o de todo el colegio)."""
    dia = (
        DiaSinClases.objects.filter(fecha=fecha)
        .filter(Q(curso__isnull=True) | Q(curso=curso))
        .first()
    )
    if dia:
        motivo = f': {dia.motivo}' if dia.motivo else ''
        raise serializers.ValidationError(f'Ese día está marcado sin clases{motivo}.')


class AsistenciaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)

    class Meta:
        model = Asistencia
        fields = ['id', 'alumno', 'alumno_nombre', 'curso', 'curso_nombre', 'fecha', 'presente']
        read_only_fields = ['id']

    def get_alumno_nombre(self, obj):
        return obj.alumno.get_full_name() or obj.alumno.username

    def validate(self, attrs):
        alumno = attrs.get('alumno', getattr(self.instance, 'alumno', None))
        curso = attrs.get('curso', getattr(self.instance, 'curso', None))
        fecha = attrs.get('fecha', getattr(self.instance, 'fecha', None))

        if not Inscripcion.objects.filter(alumno=alumno, curso=curso).exists():
            raise serializers.ValidationError('El alumno no está inscripto en ese curso.')

        validar_acceso_al_curso(self.context['request'].user, curso)
        validar_dia_con_clases(curso, fecha)
        return attrs


class RegistroAsistenciaSerializer(serializers.Serializer):
    alumno = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.filter(rol=Rol.ALUMNO))
    presente = serializers.BooleanField()


class TomarAsistenciaSerializer(serializers.Serializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all())
    fecha = serializers.DateField()
    registros = RegistroAsistenciaSerializer(many=True, allow_empty=False)

    def validate_fecha(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('No se puede registrar asistencia en una fecha futura.')
        return value

    def validate(self, attrs):
        curso = attrs['curso']
        validar_acceso_al_curso(self.context['request'].user, curso)
        validar_dia_con_clases(curso, attrs['fecha'])

        ids = [r['alumno'].id for r in attrs['registros']]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Hay alumnos repetidos en la lista.')

        inscriptos = set(
            Inscripcion.objects.filter(curso=curso, alumno_id__in=ids)
            .values_list('alumno_id', flat=True)
        )
        if any(i not in inscriptos for i in ids):
            raise serializers.ValidationError('Hay alumnos que no están inscriptos en ese curso.')
        return attrs


class DiaSinClasesSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.SerializerMethodField()
    reemplazar = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = DiaSinClases
        fields = ['id', 'fecha', 'curso', 'curso_nombre', 'motivo', 'reemplazar']
        read_only_fields = ['id']
        validators = []  # las unicidades se validan a mano (una de ellas es condicional)

    def get_curso_nombre(self, obj):
        return obj.curso.nombre if obj.curso_id else None

    def validate(self, attrs):
        user = self.context['request'].user
        curso = attrs.get('curso')
        fecha = attrs['fecha']
        es_admin = es_direccion(user)

        if curso is None:
            if not es_admin:
                raise serializers.ValidationError(
                    'Solo el administrador puede marcar un día sin clases para todo el colegio.'
                )
            if DiaSinClases.objects.filter(fecha=fecha, curso__isnull=True).exists():
                raise serializers.ValidationError('Ese día ya está marcado sin clases para todo el colegio.')
            hay_asistencia = Asistencia.objects.filter(fecha=fecha).exists()
        else:
            validar_acceso_al_curso(user, curso)
            ya_marcado = (
                DiaSinClases.objects.filter(fecha=fecha)
                .filter(Q(curso__isnull=True) | Q(curso=curso))
                .exists()
            )
            if ya_marcado:
                raise serializers.ValidationError('Ese día ya está marcado sin clases.')
            hay_asistencia = Asistencia.objects.filter(fecha=fecha, curso=curso).exists()

        if hay_asistencia and not attrs.get('reemplazar'):
            raise serializers.ValidationError('Ya hay asistencia cargada ese día. Confirmá para reemplazarla.')
        return attrs

    def create(self, validated_data):
        reemplazar = validated_data.pop('reemplazar', False)
        with transaction.atomic():
            if reemplazar:
                registros = Asistencia.objects.filter(fecha=validated_data['fecha'])
                if validated_data.get('curso'):
                    registros = registros.filter(curso=validated_data['curso'])
                registros.delete()
            return super().create(validated_data)