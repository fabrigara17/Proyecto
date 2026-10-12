from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        MATERIAL = 'MATERIAL', 'Material'
        CONSULTA = 'CONSULTA', 'Consulta'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.GENERAL)
    referencia_id = models.PositiveIntegerField(null=True, blank=True)  # id del material, si corresponde

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.usuario} - {self.mensaje[:30]}"