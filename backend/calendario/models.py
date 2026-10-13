from django.conf import settings
from django.db import models

from users.models import Rol


class Evento(models.Model):
    class Tipo(models.TextChoices):
        EVENTO = 'EVENTO', 'Evento'
        EXAMEN = 'EXAMEN', 'Examen'
        REUNION = 'REUNION', 'Reunión'
        AVISO = 'AVISO', 'Aviso'

    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.EVENTO)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()  # igual a fecha_inicio si dura un solo día
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='eventos_creados',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_inicio', 'hora_inicio', 'id']
        indexes = [models.Index(fields=['fecha_inicio', 'fecha_fin'])]

    def __str__(self):
        return f"{self.titulo} ({self.fecha_inicio})"


class DestinoEvento(models.Model):
    """A quién le llega un evento. Un evento puede tener varios destinos."""

    class Tipo(models.TextChoices):
        TODOS = 'TODOS', 'Toda la escuela'
        ROL = 'ROL', 'Una categoría'
        CURSO = 'CURSO', 'Un curso'

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='destinos')
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    # ROL: la categoría completa. CURSO: qué integrantes de ese curso (alumnos, familias, docentes, preceptores)
    rol = models.CharField(max_length=20, choices=Rol.choices, blank=True, default='')
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.CASCADE,
        null=True, blank=True, related_name='destinos_evento',
    )

    def __str__(self):
        return f"{self.evento} → {self.tipo} {self.rol} {self.curso or ''}"

