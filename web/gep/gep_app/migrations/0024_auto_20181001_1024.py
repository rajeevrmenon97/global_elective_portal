# Generated by Django 2.0 on 2018-10-01 10:24

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0023_auto_20181001_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='allowed_semesters',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Semester I'), (2, 'Semester II'), (3, 'Semester III'), (4, 'Semester IV'), (5, 'Semester V'), (6, 'Semester VI'), (7, 'Semester VII'), (8, 'Semester VIII'), (9, 'Semester IX'), (10, 'Semester X')]), blank=True, default=[], size=None),
        ),
    ]