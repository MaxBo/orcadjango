# Generated by Django 3.0 on 2020-02-06 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orcaserver', '0014_auto_20200206_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='injectable',
            name='groupname',
            field=models.TextField(default=''),
        ),
    ]