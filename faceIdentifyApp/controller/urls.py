from django.urls import path
from . import views

urlpatterns = [
  path('', views.info, name='info'),
  path('repro', views.repro, name='repro'),
  path('prev', views.prev, name='prev'),
  path('test_place', views.testPlace, name='testPlace'),
  path('show_calc_info', views.showCalcInfo, name='showCalcInfo'),
  path('edit_calc_info/<int:id>', views.editCalcInfo, name='editCalcInfo'),
  path('show_result', views.showResult, name='showResult'),
  path('add_result', views.addResult, name='addResult'),
  path('show_prev_info', views.showPrevInfo, name='showPrevInfo'),
  path('edit_prev_info', views.editPrevInfo, name='editPrevInfo'),
]
