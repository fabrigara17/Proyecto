from django.conf import settings
from django.db import models


class Comunicacion(models.Model):
    class Tipo(models.TextChoices):
        AVISO = 'AVISO', 'Aviso'
        COMUNICADO = 'COMUNICADO', 'Comunicado'
        ACTIVIDAD = 'ACTIVIDAD', 'Actividad'
        ACTO = 'ACTO', 'Acto'
        REUNION = 'REUNION', 'Reunión'

    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comunicaciones')
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.AVISO)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class ComunicacionVista(models.Model):
    """Registro de que un usuario abrió un comunicado."""
    comunicacion = models.ForeignKey(Comunicacion, on_delete=models.CASCADE, related_name='vistas')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comunicaciones_vistas',
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['comunicacion', 'usuario'], name='uniq_vista_comunicacion_usuario'),
        ]

    def __str__(self):
        return f"{self.usuario} vio {self.comunicacion}"