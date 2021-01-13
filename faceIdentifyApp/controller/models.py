from django.db import models
from django.utils import timezone

# Create your models here.

class CalcInfo(models.Model):
  name = models.CharField(max_length=100)
  ip_addr = models.CharField(max_length=100)
  local_addr = models.CharField(max_length=100)
  bandwidth = models.FloatField(max_length=100)
  delay = models.FloatField(max_length=100)

  def __str__(self):
    return '<calc: name={}, ip_addr={}>'.format(self.name, self.ip_addr)

# 実行結果を保存するためのモデル
class Result(models.Model):
  client_id = models.CharField(max_length=100)
  ip_addr = models.CharField(max_length=100)
  alg = models.CharField(max_length=100)
  pre = models.FloatField(max_length=100)
  result = models.FloatField(max_length=100)
  input_name = models.CharField(max_length=100)
  input_size = models.FloatField(max_length=100)
  ans = models.CharField(max_length=100)
  confidence = models.FloatField(max_length=100)
  pre_task1 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  pre_task2 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  pre_task3 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  res_task1 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  res_task2 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  res_task3 = models.FloatField(max_length=100) # calc_name:trans_time:run_time
  datetime = models.DateTimeField(default=timezone.now)

  def __str__(self):
    return '<client_id: {}, ip_addr: {}, pre: {}, res: {}>'.format(self.client_id, self.ip_addr, self.prediction, self.result)

# 1つ前の結果を記録するためのモデル
# 入力データのデータサイズを考慮した値を入れる
class PrevInfo(models.Model):
  prev_id = models.IntegerField()
  latest_id = models.CharField(max_length=100)
  latest_addr = models.CharField(max_length=100)
  client_task1 = models.FloatField(max_length=100)
  client_task2 = models.FloatField(max_length=100)
  edge_task1 = models.FloatField(max_length=100)
  edge_task2 = models.FloatField(max_length=100)
  edge_task3 = models.FloatField(max_length=100)
  cloud_task1 = models.FloatField(max_length=100)
  cloud_task2 = models.FloatField(max_length=100)
  cloud_task3 = models.FloatField(max_length=100)
  client_edge = models.FloatField(max_length=100)
  client_cloud = models.FloatField(max_length=100)
  edge_cloud = models.FloatField(max_length=100)

  def __str__(self):
    return '<client_id: {}, ip_addr: {}>'.format(self.latest_id, self.latest_addr)

