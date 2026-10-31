from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Rol, Usuario, roles_gestionables


class UsuarioSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'rol', 'rol_display', 'debe_cambiar_password']
        read_only_fields = ['id', 'debe_cambiar_password']


class PerfilSerializer(UsuarioSerializer):
    """Datos del usuario logueado (login y /perfil). Suma el curso si es alumno."""
    curso = serializers.SerializerMethodField()

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ['curso']

    def get_curso(self, obj):
        if obj.rol != Rol.ALUMNO:
            return None
        # Import local para evitar dependencia circular entre apps
        from academico.models import Inscripcion
        inscripcion = (
            Inscripcion.objects.filter(alumno=obj)
            .select_related('curso')
            .order_by('-curso__anio_lectivo')
            .first()
        )
        return inscripcion.curso.nombre if inscripcion else None


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True)

    def validate_password_actual(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual no es correcta.')
        return value

    def validate_password_nueva(self, value):
        try:
            validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Alta y edición de usuarios por quien tenga permiso de gestión (ver roles_gestionables)."""
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    ultima_conexion = serializers.DateTimeField(source='last_login', read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email',
                  'rol', 'rol_display', 'is_active', 'debe_cambiar_password',
                  'ultima_conexion', 'password']
        read_only_fields = ['id', 'debe_cambiar_password']

    def validate_rol(self, value):
        if value not in roles_gestionables(self.context['request'].user):
            raise serializers.ValidationError('No tenés permiso para crear usuarios con ese rol.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.debe_cambiar_password = True
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
            instance.debe_cambiar_password = True
        instance.save()
        return instance