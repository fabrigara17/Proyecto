from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Curso(models.Model):
    nombre = models.CharField(max_length=50)  # "6°M"
    anio_cursada = models.PositiveSmallIntegerField(
        'año de cursada', null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )  # 1 a 7: "6to año"
    anio_lectivo = models.PositiveSmallIntegerField('año lectivo')

    class Meta:
        ordering = ['-anio_lectivo', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['nombre', 'anio_lectivo'], name='uniq_curso_anio'),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.anio_lectivo})"

class Materia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MateriaCurso(models.Model):
    """Plan de estudios: qué materias tiene cada curso."""
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='plan')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='planes')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['curso', 'materia'], name='uniq_materia_curso'),
        ]

    def __str__(self):
        return f"{self.materia} - {self.curso}"


class Inscripcion(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='inscripciones', limit_choices_to={'rol': 'ALUMNO'},
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='inscripciones')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['alumno', 'curso'], name='uniq_inscripcion'),
        ]

    def __str__(self):
        return f"{self.alumno} → {self.curso}"


class AsignacionDocente(models.Model):
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='asignaciones', limit_choices_to={'rol': 'DOCENTE'},
    )
    materia_curso = models.ForeignKey(
        MateriaCurso, on_delete=models.CASCADE, related_name='asignaciones',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['docente', 'materia_curso'], name='uniq_asignacion'),
        ]

    def __str__(self):
        return f"{self.docente} - {self.materia_curso}"


class VinculoFamiliar(models.Model):
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='alumnos_a_cargo', limit_choices_to={'rol': 'FAMILIA'},
    )
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tutores', limit_choices_to={'rol': 'ALUMNO'},
    )
    parentesco = models.CharField(max_length=30, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tutor', 'alumno'], name='uniq_vinculo'),
        ]

    def __str__(self):
        return f"{self.tutor} ↔ {self.alumno}"

class AsignacionPreceptor(models.Model):
    preceptor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cursos_a_cargo', limit_choices_to={'rol': 'PRECEPTOR'},
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='preceptores')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['preceptor', 'curso'], name='uniq_asignacion_preceptor'),
        ]

    def __str__(self):
        return f"{self.preceptor} → {self.curso}"