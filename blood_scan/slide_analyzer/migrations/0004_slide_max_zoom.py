# Generated by Django 4.1.7 on 2023-03-22 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide_analyzer', '0003_slide'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='max_zoom',
            field=models.IntegerField(default=5),
            preserve_default=False,
        ),
    ]
