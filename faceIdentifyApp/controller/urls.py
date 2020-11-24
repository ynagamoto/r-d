from django.urls import path
from . import views

urlpatterns = [
  path('', views.controller, name='controller'),
  path('test_place', views.testPlace, name='testPlace'),
  path('test_client', views.testClient, name='testClient'),
]
