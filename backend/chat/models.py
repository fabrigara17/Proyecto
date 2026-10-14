from django.db import models
from users.models import Usuario


def ruta_adjunto(instance, filename):
    return f"chat/conversacion_{instance.conversacion_id}/{filename}"


class Conversacion(models.Model):
    # Participantes de la charla
    participante_1 = models.ForeignKey(Usuario, related_name='conversaciones_iniciadas', on_delete=models.CASCADE)
    participante_2 = models.ForeignKey(Usuario, related_name='conversaciones_recibidas', on_delete=models.CASCADE)
    
    # Para manejar solicitudes (Ej: si un alumno inicia una charla, nace como pendiente)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de aprobación'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='aceptada')
    
    # Quién envió la solicitud (para saber quién espera aprobación)
    iniciado_por = models.ForeignKey(Usuario, related_name='solicitudes_enviadas', on_delete=models.CASCADE)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat entre {self.participante_1} y {self.participante_2} ({self.estado})"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, related_name='mensajes', on_delete=models.CASCADE)
    remisor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField(blank=True)
    archivo = models.FileField(upload_to=ruta_adjunto, blank=True)
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"De {self.remisor}: {self.texto[:20] or self.archivo.name}"