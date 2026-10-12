from django.contrib import admin
from .models import (
    Curso, Materia, MateriaCurso, Inscripcion, AsignacionDocente,
    AsignacionPreceptor, VinculoFamiliar,
)


class MateriaCursoInline(admin.TabularInline):
    model = MateriaCurso
    extra = 1


class AsignacionPreceptorInline(admin.TabularInline):
    model = AsignacionPreceptor
    extra = 1


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    inlines = [MateriaCursoInline, AsignacionPreceptorInline]


admin.site.register(Materia)
admin.site.register(Inscripcion)
admin.site.register(AsignacionDocente)
admin.site.register(AsignacionPreceptor)
admin.site.register(VinculoFamiliar)