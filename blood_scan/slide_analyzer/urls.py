from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('home', views.home, name='home'),
    path('wbc_view', views.wbc_view, name='wbc_view'),
    path('slide_view', views.slide_view, name='slide_view'),
    path('upload', views.upload, name='upload'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
