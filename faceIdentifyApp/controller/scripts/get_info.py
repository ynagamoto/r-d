import requests
import json
import subprocess

def getCpuUsage(ip_addr):
  url = 'http://{}/calculator/info'.format(ip_addr)
  res_j = requests.get(url)
  res = json.loads(res_j.text)
  return res['cpu usage']

def getNwBw(ip_addr):
  command = 'iperf3 -c {} -JZ -t1'.format(ip_addr)

  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  res_j = json.loads(res.decode())
  return res_j['end']['sum_sent']['bits_per_second'] 

def getNwDelay(ip_addr):
  n = 1
  command = 'ping -c{} -i0.2 {}'.format(n, ip_addr)

  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  ave = res.decode().splitlines()[-1].split('=')[-1].split('/')[1]
  return ave

