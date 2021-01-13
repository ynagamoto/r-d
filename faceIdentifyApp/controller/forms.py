from django import forms
from .models import CalcInfo,Result,PrevInfo

class CalcInfoForm(forms.ModelForm):
  class Meta:
    model = CalcInfo
    fields = [
      'ip_addr',
      'local_addr',
    ]

class ResultForm(forms.ModelForm):
  class Meta:
    model = Result
    fields = [
      'client_id',
      'ip_addr',
      'alg',
      'pre',
      'result',
      'input_name',
      'input_size',
      'ans',
      'confidence',
      'pre_task1',
      'pre_task2',
      'pre_task3',
      'res_task1',
      'res_task2',
      'res_task3',
    ]

class PrevInfoForm(forms.ModelForm):
  class Meta:
    model = PrevInfo
    fields = [
      'latest_id',
      'latest_addr',
      'client_task1',
      'client_task2',
      'edge_task1',
      'edge_task2',
      'edge_task3',
      'cloud_task1',
      'cloud_task2',
      'cloud_task3',
      'client_edge',
      'client_cloud',
      'edge_cloud',
    ]

