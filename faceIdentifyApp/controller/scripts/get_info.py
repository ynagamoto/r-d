import requests
import json
import subprocess
import threading

def getCpuU(ip_addr, result):
  url = 'http://{}/calculator/info'.format(ip_addr)
  res_j = requests.post(url)
  res = json.loads(res_j.text)
  result['cpu'] = float(res['cpu'])

def getNwBw(ip_addr, result):
  # command = 'iperf3 -c {} -JZ -t1'.format(ip_addr)
  command = 'iperf -c {} -t 0.2'.format(ip_addr)
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  # res_j = json.loads(res.decode())
  # bps = res_j['end']['sum_sent']['bits_per_second'] 
  bps = res.decode().splitlines()[-1].rsplit(' ', 2)[-2]
  result['bw'] = float(bps)

def getPing(ip_addr, result):
  n = 1
  command = 'ping -c{} -i0.2 {}'.format(n, ip_addr)
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
  ave = res.decode().splitlines()[-1].split('=')[-1].split('/')[1]
  result['ping'] = float(ave)

def getCalcInfo(ip_addr, result):
  cpu = threading.Thread(target=getCpuU, args=(ip_addr, result))
  bw = threading.Thread(target=getNwBw, args=(ip_addr, result))
  ping = threading.Thread(target=getPing, args=(ip_addr, result))
  cpu.start()
  bw.start()
  ping.start()
  cpu.join()
  bw.join()
  ping.join()
  
def getECInfo(ip_addr): 
  edge_info = {}
  cloud_info = {}
  edge = threading.Thread(target=getCalcInfo, args=(ip_addr['edge'], edge_info))
  cloud = threading.Thread(target=getCalcInfo, args=(ip_addr['cloud'], cloud_info))
  edge.start()
  cloud.start()
  edge.join()
  cloud.join()
  result = {
    'edge': edge_info,
    'cloud': cloud_info,
  }
  return result
