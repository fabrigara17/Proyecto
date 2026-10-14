from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from academico.models import AsignacionDocente, AsignacionPreceptor, Inscripcion
from users.models import Rol, Usuario, es_direccion
from .models import Asistencia, DiaSinClases, Estado, HorarioClase


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


def validar_acceso_a_clase(user, clase):
    """Toman asistencia de una clase el preceptor del curso o el docente de esa materia."""
    if user.is_superuser:
        return
    if user.rol == Rol.PRECEPTOR:
        tiene = AsignacionPreceptor.objects.filter(preceptor=user, curso=clase.curso).exists()
    elif user.rol == Rol.DOCENTE:
        tiene = AsignacionDocente.objects.filter(
            docente=user, materia_curso=clase.materia_curso,
        ).exists()
    else:
        tiene = False
    if not tiene:
        raise serializers.ValidationError('No tenés asignada esa clase.')


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


def validar_dia_abierto(fecha):
    """La asistencia solo se registra y se corrige el mismo día: al terminar queda cerrada."""
    hoy = timezone.localdate()
    if fecha > hoy:
        raise serializers.ValidationError('No se puede registrar asistencia en una fecha futura.')
    if fecha < hoy:
        raise serializers.ValidationError(
            'Ese día ya terminó: la asistencia quedó cerrada y no se puede modificar.'
        )


class AsistenciaSerializer(serializers.ModelSerializer):
    """Solo lectura: la asistencia se carga con la acción "tomar"."""
    alumno_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    materia_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    hora_inicio = serializers.SerializerMethodField()
    hora_fin = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = [
            'id', 'alumno', 'alumno_nombre', 'curso', 'curso_nombre',
            'clase', 'materia_curso', 'materia_nombre', 'hora_inicio', 'hora_fin',
            'fecha', 'estado', 'estado_display', 'presente',
        ]
        read_only_fields = fields

    def get_alumno_nombre(self, obj):
        return obj.alumno.get_full_name() or obj.alumno.username

    def get_materia_nombre(self, obj):
        return obj.materia_curso.materia.nombre if obj.materia_curso_id else None

    def get_hora_inicio(self, obj):
        return obj.clase.hora_inicio.strftime('%H:%M') if obj.clase_id else None

    def get_hora_fin(self, obj):
        return obj.clase.hora_fin.strftime('%H:%M') if obj.clase_id else None


class RegistroAsistenciaSerializer(serializers.Serializer):
    alumno = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.filter(rol=Rol.ALUMNO))
    estado = serializers.ChoiceField(choices=Estado.choices)


class TomarAsistenciaSerializer(serializers.Serializer):
    clase = serializers.PrimaryKeyRelatedField(
        queryset=HorarioClase.objects.select_related('curso', 'materia_curso__materia'),
    )
    fecha = serializers.DateField()
    registros = RegistroAsistenciaSerializer(many=True, allow_empty=False)

    def validate_fecha(self, value):
        validar_dia_abierto(value)
        return value

    def validate(self, attrs):
        clase = attrs['clase']
        fecha = attrs['fecha']
        curso = clase.curso

        if fecha.weekday() != clase.dia_semana:
            raise serializers.ValidationError('Esa clase no se dicta en ese día de la semana.')
        validar_acceso_a_clase(self.context['request'].user, clase)
        validar_dia_con_clases(curso, fecha)

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


class HorarioClaseSerializer(serializers.ModelSerializer):
    hora_inicio = serializers.TimeField(format='%H:%M')
    hora_fin = serializers.TimeField(format='%H:%M')
    materia_nombre = serializers.CharField(source='materia_curso.materia.nombre', read_only=True)
    dia_display = serializers.CharField(source='get_dia_semana_display', read_only=True)
    docentes = serializers.SerializerMethodField()

    class Meta:
        model = HorarioClase
        fields = [
            'id', 'curso', 'materia_curso', 'materia_nombre',
            'dia_semana', 'dia_display', 'hora_inicio', 'hora_fin', 'docentes',
        ]
        read_only_fields = ['id']

    def get_docentes(self, obj):
        return [
            a.docente.get_full_name() or a.docente.username
            for a in obj.materia_curso.asignaciones.all()
        ]

    def validate(self, attrs):
        g = lambda k: attrs.get(k, getattr(self.instance, k, None))
        curso, materia_curso = g('curso'), g('materia_curso')
        dia, inicio, fin = g('dia_semana'), g('hora_inicio'), g('hora_fin')

        if materia_curso.curso_id != curso.id:
            raise serializers.ValidationError(
                {'materia_curso': 'Esa materia no pertenece al plan de ese curso.'}
            )
        if fin <= inicio:
            raise serializers.ValidationError('La hora de fin debe ser posterior a la de inicio.')

        validar_acceso_al_curso(self.context['request'].user, curso)

        choque = HorarioClase.objects.filter(
            curso=curso, dia_semana=dia, hora_inicio__lt=fin, hora_fin__gt=inicio,
        )
        if self.instance is not None:
            choque = choque.exclude(pk=self.instance.pk)
        if choque.exists():
            raise serializers.ValidationError('Se superpone con otra clase de ese curso ese día.')
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

        if hay_asistencia and fecha < timezone.localdate():
            raise serializers.ValidationError(
                'Ese día ya terminó y tiene asistencia registrada: no se puede modificar.'
            )
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