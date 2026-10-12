from django.conf import settings
from django.db import models


class Asistencia(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='asistencias', limit_choices_to={'rol': 'ALUMNO'},
    )
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.PROTECT, related_name='asistencias',
    )
    fecha = models.DateField()
    presente = models.BooleanField(default=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='asistencias_registradas',
    )

    class Meta:
        ordering = ['-fecha', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'curso', 'fecha'],
                name='uniq_asistencia_alumno_curso_fecha',
            ),
        ]

    def __str__(self):
        return f"{self.alumno} - {self.curso} - {self.fecha}"

class DiaSinClases(models.Model):
    """Día sin clases (feriado, ausencia docente, etc.). Sin curso = vale para todo el colegio."""
    fecha = models.DateField()
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.CASCADE, null=True, blank=True,
        related_name='dias_sin_clases',
    )
    motivo = models.CharField(max_length=100, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='dias_sin_clases_registrados',
    )

    class Meta:
        ordering = ['-fecha', 'id']
        verbose_name_plural = 'días sin clases'
        constraints = [
            models.UniqueConstraint(fields=['fecha', 'curso'], name='uniq_sin_clases_fecha_curso'),
            # En PostgreSQL los NULL son distintos entre sí, así que el "todo el colegio" necesita su propia regla
            models.UniqueConstraint(
                fields=['fecha'], condition=models.Q(curso__isnull=True),
                name='uniq_sin_clases_fecha_general',
            ),
        ]

    def __str__(self):
        alcance = self.curso.nombre if self.curso_id else 'Todo el colegio'
        return f"{self.fecha} - {alcance}"