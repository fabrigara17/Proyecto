from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Etapa(models.Model):
    """Período del año lectivo (ej. "1er trimestre") en el que los docentes pueden cargar y modificar notas.
    El equipo de conducción define las fechas y puede abrirla o cerrarla."""
    nombre = models.CharField(max_length=50)
    anio_lectivo = models.PositiveSmallIntegerField('año lectivo')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    habilitada = models.BooleanField(default=True)

    class Meta:
        ordering = ['-anio_lectivo', 'fecha_inicio']
        constraints = [
            models.UniqueConstraint(fields=['nombre', 'anio_lectivo'], name='uniq_etapa_nombre_anio'),
        ]

    @property
    def esta_abierta(self):
        """Se pueden cargar notas si está habilitada y hoy cae dentro de sus fechas."""
        return self.habilitada and self.fecha_inicio <= timezone.localdate() <= self.fecha_fin

    def __str__(self):
        return f"{self.nombre} ({self.anio_lectivo})"


class Calificacion(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='calificaciones', limit_choices_to={'rol': 'ALUMNO'},
    )
    materia = models.ForeignKey(
        'academico.Materia', on_delete=models.PROTECT, related_name='calificaciones',
    )
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.PROTECT, related_name='calificaciones',
    )
    etapa = models.ForeignKey(
        Etapa, on_delete=models.PROTECT, related_name='calificaciones',
        null=True, blank=True,  # null: notas cargadas antes de que existieran las etapas
    )
    nota = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],  # escala 1–10: ajustala si usan otra
    )
    detalle = models.CharField(max_length=100, blank=True)  # ej. "Parcial 1", "TP final"
    fecha = models.DateField()
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='calificaciones_cargadas',
    )

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.alumno} - {self.materia}: {self.nota}"