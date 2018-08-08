# Generated by Django 2.0 on 2018-08-08 13:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0006_auto_20180808_1135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='next_semester',
            field=models.IntegerField(blank=True, choices=[(1, 'Semester I'), (2, 'Semester II'), (3, 'Semester III'), (4, 'Semester IV'), (5, 'Semester V'), (6, 'Semester VI'), (7, 'Semester VII'), (8, 'Semester VIII'), (9, 'Semester IX'), (10, 'Semester X')], null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
    ]
