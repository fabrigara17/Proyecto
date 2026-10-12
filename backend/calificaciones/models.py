from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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
    nota = models.DecimalField(
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(1), MaxValueValidator(10)],  # escala 1–10: ajustala si usan otra
    )
    fecha = models.DateField()
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='calificaciones_cargadas',
    )

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.alumno} - {self.materia}: {self.nota}"