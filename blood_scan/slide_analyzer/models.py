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

class MicroscopeUse(models.Model):
    ip = models.TextField()
    slide = models.IntegerField()
    current_wbc = models.IntegerField()
    target_wbc = models.IntegerField()
    current_field = models.IntegerField()
    target_field = models.IntegerField()
    in_use = models.BooleanField()
