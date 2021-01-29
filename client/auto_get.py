import requests
import json
import subprocess
from multiprocessing import Process,Value,Array
#import threading
import MySQLdb

def getNwBw(ip_addr, result):
  #command = 'iperf3 -c {} -JZ -t1'.format(ip_addr)
  command = 'iperf -c {} -t 0.5'.format(ip_addr)
  flag = False
  while not flag:
    try:
      res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
      # res_j = json.loads(res.decode())
      # bps = res_j['end']['sum_sent']['bits_per_second'] 
      bps = res.decode().splitlines()[-1].rsplit(' ', 2)[-2]
      if res.decode().splitlines()[-1].rsplit(' ', 2)[-1][0] == 'G': 
        bps = float(bps)*1000.0
      flag = True
      result.value = float(bps)
    except Exception as e:
      print(e)

def getNwDelay(ip_addr, result):
  n = 3
  command = 'ping -c{} {}'.format(n, ip_addr)
  flag = False
  while not flag:
    try:
      res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, check=True).stdout
      ave = res.decode().splitlines()[-1].split('=')[-1].split('/')[1]
      flag = True
      result.value = float(ave)
    except Exception as e:
      print(e)

# データベースに接続
conn = MySQLdb.connect(
  user = 'django_user',
  passwd = 'C%ZnBP$jQian',
  host = 'localhost',
  db = 'face_identify_app',
)

# データベースからcloudのIPアドレスと取得
ip_addr = {}
cur = conn.cursor()
sql = "select ip_addr from controller_calcinfo where name='edge';"
cur.execute(sql)
row = cur.fetchone()
ip_addr['edge'] = row[0]

sql = "select ip_addr from controller_calcinfo where name='cloud';"
cur.execute(sql)
row = cur.fetchone()
ip_addr['cloud'] = row[0]


# 各種情報を取得
calcs = ['edge', 'cloud']
info = {
  calcs[0]: {
    'bw': Value('f', 0.0),
    'ping': Value('f', 0.0),
  },
  calcs[1]: {
    'bw': Value('f', 0.0),
    'ping': Value('f', 0.0),
  },
}

# 並列で実行
tasks ={
  calcs[0]: [],
  calcs[1]: [],
}
for calc in calcs:
  tasks[calc].append(Process(target=getNwBw, args=(ip_addr[calc], info[calc]['bw'])))
  tasks[calc].append(Process(target=getNwDelay, args=(ip_addr[calc], info[calc]['ping'])))
for calc in calcs:
  for i in range(len(tasks[calc])):
    tasks[calc][i].start()
for calc in calcs:
  for i in range(len(tasks[calc])):
    tasks[calc][i].join()
    

# 結果をデータベースへ
for calc in calcs:
  sql = "update controller_calcinfo set bandwidth=%s,delay=%s where name=%s;"
  cur.execute(sql, [info[calc]['bw'].value, info[calc]['ping'].value, calc])

conn.commit()
cur.close
conn.close

