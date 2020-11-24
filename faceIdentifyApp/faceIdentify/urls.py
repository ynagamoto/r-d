from django.urls import path
from . import views

urlpatterns = [
  path('', views.index),
  path('index', views.index, name="index"),
  path('faceIdentify', views.faceIdentify, name='faceIdentify'),
  path('getFace', views.getFace, name='getFace'),
  path('prepImage', views.prepImage, name='prepImage'),
  path('faceMatching', views.faceMatching, name='faceMatching'),
  path('selectPlace', views.selectPlace, name='selectPlace'),
]
