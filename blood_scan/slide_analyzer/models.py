from django.db import models
import os

class WBCImg(models.Model):
    type = models.CharField(max_length=50)
    slide = models.IntegerField()
    src = models.CharField(max_length=50)
    imgID = models.IntegerField()
    lat = models.FloatField()
    lng = models.FloatField()
    lat_upper = models.FloatField()
    lng_upper = models.FloatField()
    lat_lower = models.FloatField()
    lng_lower = models.FloatField()

    def make_slide_for_test():
        wbc_img_lst = os.listdir("slide/1")
        for wbc_img in wbc_img_lst:
            WBCImg(type="none", slide=1)

class WBCDiffConfig(models.Model):
    type = models.CharField(max_length=50)
    parent = models.CharField(max_length=50)
    key_bind = models.IntegerField(null=True)

class MorphologyConfig(models.Model):
    type = models.CharField(max_length=50)
    parent = models.CharField(max_length=50)
    quantitative = models.BooleanField()

class Slide(models.Model):
    number = models.IntegerField()
    morphology = models.TextField()
    max_zoom = models.IntegerField()
    coordinate_factors = models.CharField(max_length=100)
