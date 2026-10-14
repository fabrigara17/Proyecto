from django.contrib import admin
from .models import Asistencia, DiaSinClases, HorarioClase

admin.site.register(Asistencia)
admin.site.register(DiaSinClases)
admin.site.register(HorarioClase)