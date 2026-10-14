import django.db.models.deletion
from django.db import migrations, models


def marcar_ausentes(apps, schema_editor):
    """Los registros viejos tenían solo presente/ausente: los ausentes pasan a estado AUSENTE."""
    Asistencia = apps.get_model('asistencias', 'Asistencia')
    Asistencia.objects.filter(presente=False).update(estado='AUSENTE')


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0006_curso_turno'),
        ('asistencias', '0003_diasinclases'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorarioClase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.PositiveSmallIntegerField(choices=[(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), (4, 'Viernes')])),
                ('hora_inicio', models.TimeField()),
                ('hora_fin', models.TimeField()),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios', to='academico.curso')),
                ('materia_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios', to='academico.materiacurso')),
            ],
            options={
                'verbose_name_plural': 'horarios de clase',
                'ordering': ['dia_semana', 'hora_inicio'],
            },
        ),
        migrations.AddField(
            model_name='asistencia',
            name='estado',
            field=models.CharField(choices=[('PRESENTE', 'Presente'), ('AUSENTE', 'Ausente'), ('TARDE', 'Llegada tarde'), ('RETIRO', 'Retiro anticipado')], default='PRESENTE', max_length=10),
        ),
        migrations.AddField(
            model_name='asistencia',
            name='clase',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asistencias', to='asistencias.horarioclase'),
        ),
        migrations.AddField(
            model_name='asistencia',
            name='materia_curso',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asistencias', to='academico.materiacurso'),
        ),
        migrations.RemoveConstraint(
            model_name='asistencia',
            name='uniq_asistencia_alumno_curso_fecha',
        ),
        migrations.AddConstraint(
            model_name='asistencia',
            constraint=models.UniqueConstraint(fields=('alumno', 'clase', 'fecha'), name='uniq_asistencia_alumno_clase_fecha'),
        ),
        migrations.RunPython(marcar_ausentes, migrations.RunPython.noop),
    ]