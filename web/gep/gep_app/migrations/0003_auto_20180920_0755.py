# Generated by Django 2.0 on 2018-09-20 07:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0002_auto_20180919_1338'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student',
            old_name='current_CGPA',
            new_name='current_cgpa',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='FA',
            new_name='faculty_advisor',
        ),
    ]