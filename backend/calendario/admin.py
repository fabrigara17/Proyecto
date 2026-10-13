from django.contrib import admin
from .models import DestinoEvento, Evento


class DestinoInline(admin.TabularInline):
    model = DestinoEvento
    extra = 0


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_inicio', 'fecha_fin', 'creado_por')
    inlines = [DestinoInline]