# Generated by Django 3.0 on 2020-02-06 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orcaserver', '0015_auto_20200206_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='injectable',
            name='datatype',
            field=models.TextField(blank=True, null=True),
        ),
    ]
