# Generated by Django 4.1.7 on 2023-02-23 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide_analyzer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MorphologyConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
                ('parent', models.CharField(max_length=50)),
                ('quantitative', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='WBCDiffConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
                ('parent', models.CharField(max_length=50)),
            ],
        ),
    ]
