# Generated by Django 2.0 on 2018-09-20 09:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0004_course_allowed_semesters'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='allowed_semesters',
        ),
    ]
