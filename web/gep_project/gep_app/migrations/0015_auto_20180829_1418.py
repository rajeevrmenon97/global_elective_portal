# Generated by Django 2.0 on 2018-08-29 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gep_app', '0014_auto_20180829_1019'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Student_COT_Allotment',
            new_name='COT_Allotment',
        ),
        migrations.RenameModel(
            old_name='Student_Elective_Allotment',
            new_name='Elective_Allotment',
        ),
        migrations.RenameModel(
            old_name='Student_Elective_Preference',
            new_name='Elective_Preference',
        ),
        migrations.RenameField(
            model_name='student',
            old_name='no_of_global_electives',
            new_name='required_elective_count',
        ),
    ]
