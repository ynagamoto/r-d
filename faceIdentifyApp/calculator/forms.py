from django import forms
from .models import TaskInfo

class TaskForm(forms.ModelForm):
  class Meta:
    model = TaskInfo
    fields = [
      'client_id',
      'task_id',
      'next_task',
      'next_url',
    ]
