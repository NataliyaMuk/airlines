# Generated by Django 4.2.5 on 2023-09-23 15:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='sessions',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('session_start', models.DateField()),
                ('last_confirmation', models.DateField(null=True)),
                ('error_status', models.CharField(default='Lost connection.', max_length=50, null=True)),
                ('session_end', models.DateField(null=True)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
