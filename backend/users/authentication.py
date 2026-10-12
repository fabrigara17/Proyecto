from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import TokenAuthentication


class TokenConActividad(TokenAuthentication):
    """Igual que TokenAuthentication, pero registra la última conexión (como máximo cada 5 minutos)."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        ahora = timezone.now()
        if user.last_login is None or ahora - user.last_login > timedelta(minutes=5):
            type(user).objects.filter(pk=user.pk).update(last_login=ahora)
        return user, token