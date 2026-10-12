from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import Rol, Usuario, roles_gestionables
from .permissions import PuedeGestionarUsuarios
from .serializers import (
    UsuarioSerializer, CambiarPasswordSerializer, UsuarioAdminSerializer,
)


class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return Response({
            'token': token.key,
            'usuario': UsuarioSerializer(user).data,  # incluye debe_cambiar_password
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil(request):
    return Response(UsuarioSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = request.user
    user.set_password(serializer.validated_data['password_nueva'])
    user.debe_cambiar_password = False
    user.save()

    # Rotamos el token: el anterior queda inválido tras cambiar credenciales
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)

    return Response({'token': token.key, 'mensaje': 'Contraseña actualizada correctamente'})


# Orden de los cargos, de mayor a menor
ORDEN_ROLES = Case(
    When(rol=Rol.ADMIN, then=Value(0)),
    When(rol=Rol.CONDUCCION, then=Value(1)),
    When(rol=Rol.PRECEPTOR, then=Value(2)),
    When(rol=Rol.DOCENTE, then=Value(3)),
    When(rol=Rol.FAMILIA, then=Value(4)),
    When(rol=Rol.ALUMNO, then=Value(5)),
    default=Value(9),
    output_field=IntegerField(),
)


class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioAdminSerializer
    permission_classes = [PuedeGestionarUsuarios]

    def get_queryset(self):
        user = self.request.user
        qs = Usuario.objects.filter(rol__in=roles_gestionables(user))
        q = self.request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(
            q(username__icontains=q) | q(first_name__icontains=q) | q(last_name__icontains=q)
            )
        if not user.is_superuser:
            qs = qs.exclude(is_superuser=True)  # nadie que no sea superusuario ve ni toca a un superusuario
        rol = self.request.query_params.get('rol')
        if rol:
            qs = qs.filter(rol=rol)
        return qs.annotate(orden_rol=ORDEN_ROLES).order_by('orden_rol', 'last_name', 'first_name', 'username')

    def perform_update(self, serializer):
        if (serializer.instance == self.request.user
                and serializer.validated_data.get('is_active') is False):
            raise ValidationError('No podés desactivar tu propia cuenta.')
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_superuser or user.rol == Rol.ADMIN):
            raise PermissionDenied('No podés eliminar usuarios. Podés desactivar la cuenta.')
        if instance == user:
            raise ValidationError('No podés eliminar tu propia cuenta.')
        instance.delete()