# Generated by Django 3.0.5 on 2020-04-20 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('markets', '0003_auto_20200420_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='option',
            name='question',
            field=models.TextField(blank=True),
        ),
    ]
