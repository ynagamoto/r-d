from django.db import models

# Create your models here.

class TaskInfo(models.Model):
  client_id = models.CharField(max_length=100)
  task_id = models.CharField(max_length=100)
  next_task = models.CharField(max_length=100)
  next_url = models.CharField(max_length=100)

  def __str__(self):
    return '<task: client_id={}, task_id={}, next_task={}, next_url={}>'.format(str(self.client_id), str(self.task_id), str(self.next_task), str(self.next_url))

