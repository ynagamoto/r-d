from django.urls import path
from . import views

urlpatterns = [
  path('', views.info),
  path('index', views.index, name='index'),
  path('info', views.info, name='info'),
  path('do_task', views.doTask, name='doTask'),
  path('show_task', views.showTask, name='showTask'),
  path('add_task', views.addTask, name='addTask'),
  path('edit_task/<str:cid>,<str:tid>', views.editTask, name='editTask'),
  path('delete_all_task', views.deleteAllTask, name='deleteAllTask'),
  path('delete_task/<str:cid>,<str:tid>', views.deleteTask, name='deleteTask'),
]
