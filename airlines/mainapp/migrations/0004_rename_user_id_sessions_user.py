# Generated by Django 4.2.5 on 2023-09-23 15:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0003_alter_sessions_user_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sessions',
            old_name='user_id',
            new_name='user',
        ),
    ]
