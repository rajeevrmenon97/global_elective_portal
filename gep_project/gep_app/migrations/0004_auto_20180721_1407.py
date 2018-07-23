# Generated by Django 2.0.7 on 2018-07-21 14:07

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0003_auto_20180720_1520'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student_core_slots',
            name='roll_number',
        ),
        migrations.RenameField(
            model_name='course',
            old_name='cot_status',
            new_name='cot_requisite',
        ),
        migrations.AddField(
            model_name='student',
            name='core_slots',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('P', 'P'), ('Q', 'Q'), ('R', 'R'), ('S', 'S'), ('T', 'T')], max_length=1), blank=True, null=True, size=None),
        ),
        migrations.DeleteModel(
            name='Student_Core_Slots',
        ),
    ]
