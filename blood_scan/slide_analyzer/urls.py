from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.home, name='home'),
    path('wbc_view', views.wbc_view, name='wbc_view'),
    path('slide_view', views.slide_view, name='slide_view'),
    path('upload', views.upload, name='upload'),
]
