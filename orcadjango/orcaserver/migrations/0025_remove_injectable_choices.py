# Generated by Django 3.1.3 on 2021-02-23 08:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orcaserver', '0024_injectable_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='injectable',
            name='choices',
        ),
    ]
