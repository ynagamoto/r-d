from django.db import models

# Create your models here.

class CalcInfo(models.Model):
  name = models.CharField(max_length=100)
  ip_addr = models.CharField(max_length=100)
  local_addr = models.CharField(max_length=100)
  bandwidth = models.FloatField(max_length=100)
  delay = models.FloatField(max_length=100)

  def __str__(self):
    return '<calc: name={}, ip_addr={}>'.format(self.name, self.ip_addr)

