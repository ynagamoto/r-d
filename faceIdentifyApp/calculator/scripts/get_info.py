import json
import subprocess
import psutil

def getCpuUsage(results):
  cpu_usage = float(psutil.cpu_percent(interval=0.1))
  results['cpu_u'] = cpu_usage

def getNwBw(ip_addr, results):
  command = 'iperf3 -c {} -JZ -t1'.format(ip_addr)
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  res_j = json.loads(res.decode())
  results['nw_b'] = res_j['end']['sum_sent']['bits_per_second'] 

def getNwDelay(ip_addr, results):
  command = 'ping -c{} -i0.2 {}'.format(2, ip_addr)

  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  results['nw_d'] = res.decode().splitlines()[-1].split('=')[-1].split('/')[1]

