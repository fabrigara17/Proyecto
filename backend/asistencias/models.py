from django.conf import settings
from django.db import models


class Estado(models.TextChoices):
    PRESENTE = 'PRESENTE', 'Presente'
    AUSENTE = 'AUSENTE', 'Ausente'
    TARDE = 'TARDE', 'Llegada tarde'
    RETIRO = 'RETIRO', 'Retiro anticipado'


class Dia(models.IntegerChoices):
    # Mismo número que date.weekday() de Python: lunes = 0
    LUNES = 0, 'Lunes'
    MARTES = 1, 'Martes'
    MIERCOLES = 2, 'Miércoles'
    JUEVES = 3, 'Jueves'
    VIERNES = 4, 'Viernes'


class HorarioClase(models.Model):
    """Una clase del horario semanal de un curso: qué materia se dicta, qué día y en qué horario."""
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.CASCADE, related_name='horarios',
    )
    materia_curso = models.ForeignKey(
        'academico.MateriaCurso', on_delete=models.CASCADE, related_name='horarios',
    )
    dia_semana = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        verbose_name_plural = 'horarios de clase'

    def __str__(self):
        return f"{self.curso.nombre} - {self.materia_curso.materia} - {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}"


class Asistencia(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='asistencias', limit_choices_to={'rol': 'ALUMNO'},
    )
    curso = models.ForeignKey(
        'academico.Curso', on_delete=models.PROTECT, related_name='asistencias',
    )
    fecha = models.DateField()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PRESENTE)
    # "Asistió": True salvo que esté ausente (tarde y retiro anticipado cuentan como asistencia).
    # Se mantiene por compatibilidad con los reportes que ya la usan.
    presente = models.BooleanField(default=True)
    # Asistencia por materia: la clase del horario a la que corresponde el registro.
    # Quedan en null los registros viejos (tomados por curso, sin materia).
    clase = models.ForeignKey(
        HorarioClase, on_delete=models.SET_NULL, null=True, blank=True, related_name='asistencias',
    )
    materia_curso = models.ForeignKey(
        'academico.MateriaCurso', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='asistencias',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='asistencias_registradas',
    )

    class Meta:
        ordering = ['-fecha', '-id']
        constraints = [
            # Un alumno tiene un solo registro por clase y día
            models.UniqueConstraint(
                fields=['alumno', 'clase', 'fecha'],
                name='uniq_asistencia_alumno_clase_fecha',
            ),
        ]

    def save(self, *args, **kwargs):
        # "presente" siempre se deriva del estado
        self.presente = self.estado != Estado.AUSENTE
        # update_or_create() guarda solo los campos indicados: nos aseguramos de incluir "presente"
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'presente'}
        super().save(*args, **kwargs)

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