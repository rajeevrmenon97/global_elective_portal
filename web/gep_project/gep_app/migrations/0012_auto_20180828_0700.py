# Generated by Django 2.0 on 2018-08-28 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0011_auto_20180809_0738'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Elective_Department',
            new_name='Elective_Seats',
        ),
        migrations.RenameField(
            model_name='elective_seats',
            old_name='max_count',
            new_name='max_seats',
        ),
    ]
