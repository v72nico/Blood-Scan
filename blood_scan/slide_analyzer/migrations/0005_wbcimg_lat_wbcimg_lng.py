# Generated by Django 4.1.7 on 2023-03-24 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide_analyzer', '0004_slide_max_zoom'),
    ]

    operations = [
        migrations.AddField(
            model_name='wbcimg',
            name='lat',
            field=models.FloatField(default=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wbcimg',
            name='lng',
            field=models.FloatField(default=8),
            preserve_default=False,
        ),
    ]