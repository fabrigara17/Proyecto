from django.conf import settings
from django.db import models


def ruta_material(instance, filename):
    return f"materiales/curso_{instance.materia_curso.curso_id}/{filename}"


class Material(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to=ruta_material)
    materia_curso = models.ForeignKey(
        'academico.MateriaCurso', on_delete=models.CASCADE, related_name='materiales',
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='materiales_subidos',
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name_plural = 'materiales'

    def __str__(self):
        return self.titulo

class Consulta(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='consultas')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='consultas_material',
    )
    texto = models.CharField(max_length=500)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'id']

    def __str__(self):
        return f"{self.autor}: {self.texto[:30]}"