# Generated by Django 3.0.2 on 2020-11-10 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orcaserver', '0019_injectable_parent_injectables'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='init',
            field=models.TextField(default='{}'),
        ),
        migrations.DeleteModel(
            name='GeoProject',
        ),
    ]
