from django.urls import path
from . import views

urlpatterns = [
  path('', views.info, name='info'),
  path('repro', views.repro, name='repro'),
  path('test_place', views.testPlace, name='testPlace'),
  path('show_calc_info', views.showCalcInfo, name='showCalcInfo'),
  path('edit_calc_info/<int:id>', views.editCalcInfo, name='editCalcInfo'),
]
