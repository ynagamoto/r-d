import requests
import json
import subprocess
from multiprocessing import Process,Value,Array
#import threading
import psutil
from controller.models import CalcInfo

def getCpuUsage(result):
  result.value = float(psutil.cpu_percent(interval=0.1))

def getCpuU(ip_addr, result):
  url = 'http://{}/calculator/info'.format(ip_addr)
  res_j = requests.get(url)
  res = json.loads(res_j.text)
  result.value = float(res['cpu'])

def getNwBw(ip_addr, result):
  # command = 'iperf3 -c {} -JZ -t1'.format(ip_addr)
  command = 'iperf -c {} -t 0.5'.format(ip_addr)
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  # res_j = json.loads(res.decode())
  # bps = res_j['end']['sum_sent']['bits_per_second'] 
  bps = res.decode().splitlines()[-1].rsplit(' ', 2)[-2]
  result.value = float(bps)

def getPing(ip_addr, result):
  n = 3
  # command = 'ping -c{} -i0.2 {}'.format(n, ip_addr)
  command = 'ping -c{} {}'.format(n, ip_addr)
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  ave = res.decode().splitlines()[-1].split('=')[-1].split('/')[1]
  result.value = float(ave)

def getCalcInfo(ip_addr, result):
  cpu_usage = Value('f',0.0)
  bandwidth = Value('f',0.0)
  delay = Value('f',0.0)
  cpu = Process(target=getCpuU, args=(ip_addr, cpu_usage))
  bw = Process(target=getNwBw, args=(ip_addr, bandwidth))
  ping = Process(target=getPing, args=(ip_addr, delay))
  cpu.start()
  bw.start()
  ping.start()
  cpu.join()
  bw.join()
  ping.join()
  result[0] = cpu_usage.value
  result[1] = bandwidth.value
  result[2] = delay.value
  
def getECInfo(ip_addr): 
  edge_info = Array('f', 3)
  cloud_info = Array('f', 3)
  edge = Process(target=getCalcInfo, args=(ip_addr['edge'], edge_info))
  cloud = Process(target=getCalcInfo, args=(ip_addr['cloud'], cloud_info))
  edge.start()
  cloud.start()
  edge.join()
  cloud.join()
  result = {
    'edge': {
      'cpu': edge_info[0],
      'bw': edge_info[1],
      'ping': edge_info[2],
    },
    'cloud': {
      'cpu': cloud_info[0],
      'bw': cloud_info[1],
      'ping': cloud_info[2],
    },
  }
  return result

def getECInfo2(ip_addr): 
  edge_cpu = Value('f', 0.0)
  cloud_cpu = Value('f', 0.0)
  edge = Process(target=getCpuUsage, args=(edge_cpu,))
  cloud = Process(target=getCpuU, args=(ip_addr['cloud'], cloud_cpu))
  edge.start()
  cloud.start()
  edge.join()
  cloud.join()
  edge_info = CalcInfo.objects.get(name='edge')
  cloud_info = CalcInfo.objects.get(name='cloud')
  result = {
    'edge': {
      'cpu': float(edge_cpu.value),
      'bw': float(edge_info.bandwidth),
      'ping': float(edge_info.delay),
    },
    'cloud': {
      'cpu': float(cloud_cpu.value),
      'bw': float(cloud_info.bandwidth),
      'ping': float(cloud_info.delay),
    },
  }
  return result

def getCECInfo(ip_addr):
  info = {
    'client_cpu': Value('f', 0.0),
    'edge': {
      'bw': Value('f', 0.0),
      'ping': Value('f', 0.0),
    },
    'cloud': {
      'bw': Value('f', 0.0),
      'ping': Value('f', 0.0),
    },
  }
  tasks = []
  tasks.append(Process(target=getCpuUsage, args=(info['client_cpu'],)))
  for calc in ['edge', 'cloud']:
    tasks.append(Process(target=getNwBw, args=(ip_addr[calc], info[calc]['bw'])))
    tasks.append(Process(target=getPing, args=(ip_addr[calc], info[calc]['ping'])))
  for i in range(len(tasks)):
    tasks[i].start()
  for i in range(len(tasks)):
    tasks[i].join()

  result = {
    'cpu': info['client_cpu'].value,
    'edge_bw': info['edge']['bw'].value,
    'edge_ping': info['edge']['ping'].value,
    'cloud_bw': info['cloud']['bw'].value,
    'cloud_ping': info['cloud']['ping'].value,
  }
  ''' 
  result = {
    'client': {
      'cpu': info['client_cpu'].value,
    },
    'edge': {
      'bw': info['edge']['bw'].value,
      'ping': info['edge']['ping'].value,
    },
    'cloud': {
      'bw': info['cloud']['bw'].value,
      'ping': info['cloud']['ping'].value,
    },
  }
  ''' 
  return result
