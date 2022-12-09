# Generated by Django 4.1.4 on 2022-12-09 17:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0008_auto_20221209_1949'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='appointment',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='дата и время'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='appointment',
            unique_together={('provider', 'datetime')},
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='date',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='time',
        ),
    ]
