# Generated by Django 2.2.16 on 2022-07-30 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='done_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Число когда задача выполнена'),
        ),
    ]
