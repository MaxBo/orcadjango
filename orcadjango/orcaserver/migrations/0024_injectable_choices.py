# Generated by Django 3.1.3 on 2020-11-25 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orcaserver', '0023_run'),
    ]

    operations = [
        migrations.AddField(
            model_name='injectable',
            name='choices',
            field=models.TextField(blank=True, null=True),
        ),
    ]