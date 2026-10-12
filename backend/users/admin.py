from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'rol', 'debe_cambiar_password', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Libreta Digital', {'fields': ('rol', 'debe_cambiar_password')}),
    )


admin.site.register(Usuario, UsuarioAdmin)