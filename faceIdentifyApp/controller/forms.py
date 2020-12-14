from django import forms
from .models import CalcInfo

class CalcInfoForm(forms.ModelForm):
  class Meta:
    model = CalcInfo
    fields = [
      'ip_addr',
      'local_addr',
    ]
