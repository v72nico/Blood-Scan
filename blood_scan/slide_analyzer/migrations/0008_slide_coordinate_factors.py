# Generated by Django 4.1.7 on 2023-04-01 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide_analyzer', '0007_wbcimg_lat_lower_wbcimg_lat_upper_wbcimg_lng_lower_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='coordinate_factors',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
