import requests
import cv2
import json
import base64
from multiprocessing import Process,Value
import os
import time
import socket
import asyncio
import openpyxl
from datetime import datetime

from get_info import getCECInfo
from converter import i2b
from tasks import get_face,prep_img

file_name = '../test05.png'
file_type = 'image/png'
#edge = '222.229.69.237'
edge = 'localhost:8000'
url = 'http://%s/controller/prev' % edge

# ファイルの読み込み
def open_file(file_name):
  img = cv2.imread(file_name)
  data_size = len(i2b(img)) * 8 / 1000000
  return img, data_size

# 実行先をedgeに聞いて実行 -> 結果送信
def do_task(url, context, img, data_size):
  start = time.perf_counter()
  flag = False
  while not flag:
    try:
      res_j = requests.post(url, data=context)
      flag = True
    except Exception as e:
      print(e)
  try:
    res = json.loads(res_j.text)
  except Exception as e:
    print(e)
    print('\n'+resj)
  think_time = time.perf_counter() - start

  run_all_start = time.perf_counter()
  task = 0
  times = {}
  for task_id in res['place']['client']:
    if task_id == 1:
      start = time.perf_counter()
      img = get_face(img)
      times['1'] = time.perf_counter()-start 
      task = task_id
    elif task_id == 2:
      start = time.perf_counter()
      img = prep_img(img)
      times['2'] = time.perf_counter()-start 
      task = task_id
  next_url = ''
  for calc in ['edge', 'cloud']:
    if task+1 in res['place'][calc]:
      #print('%s: %s'%(calc, res['calc_addr'][calc]))
      next_url = res['calc_addr'][calc]

  context = {
    'client_id': res['client_id'],
    'task_id': str(task+1),
    'data': i2b(img),
    'times': json.dumps(times, ensure_ascii=False, indent=2).encode('utf-8'),
  }

  place = res['place']
  calc_addr = res['calc_addr']
  pre_time = res['est_time']
  start = time.perf_counter()
  flag = False
  while not flag:
    try:
      res_j = requests.post('http://{}/calculator/do_task'.format(next_url), data=context)
      res = json.loads(res_j.text) 
      flag = True
    except Exception as e:
      print(e)
  other_run_time = time.perf_counter() - start
  run_all_time = time.perf_counter() - run_all_start

  result = {
    'client_id': res['client_id'],
    'alg': 'exis',
    'ip_addr': '222.229.69.221',
    'pre': pre_time,
    'result': run_all_time,
    'input_name': file_name,
    'input_size': float(data_size),
    'ans': str(res['label']),
    'confidence': float(res['confidence']),
    'pre_task1': 0.00,
    'pre_task2': 0.00,
    'pre_task3': 0.00,
    'res_task1': res['times']['1'],
    'res_task2': res['times']['2'],
    'res_task3': res['times']['3'],
  }

  #'''
  # 転送時間の計算
  ratio = [0.45397, 0.39966]
  for calc in place:
    for task_num in place[calc]:
      result['task'+str(task_num)+'_calc'] = calc
      result['task'+str(task_num)] = res['times'][str(task_num)]
  if (len(place['edge']) != 0) and (len(place['cloud']) != 0): # do client, edge and cloud
    #print('c-e-c')
    result['calc'] = 'c-e-c'
    result['e-c'] = res['times']['edge'+str(place['edge'][-1])]
    for task_num in place['cloud']:
      result['e-c'] -= res['times'][str(task_num)]
    result['e-c'] = data_size*(ratio[0] if 2 in place['cloud'] else ratio[0]*ratio[1])/(result['e-c']/2)
    result['c-e'] = data_size*(1 if 1 in place['edge'] else ratio[0])/((run_all_time - (res['times']['1']+res['times']['2']+res['times']['3']) - 2*result['e-c'])/2)
    result['c-c'] = result['c-e']+result['e-c']
  elif (len(place['edge']) != 0) and (len(place['cloud']) == 0): # do client and edge 
    #print('c-e')
    result['calc'] = 'c-e'
    result['c-e'] = data_size*(1 if 1 in place['edge'] else (ratio[0] if 2 in place['edge'] else ratio[1]))/((run_all_time - (res['times']['1']+res['times']['2']+res['times']['3']))/2)
  elif (len(place['cloud']) != 0) and (len(place['edge']) == 0): # do client and cloud
    #print('c-c')
    result['calc'] = 'c-c'
    result['c-c'] = data_size*(1 if 1 in place['cloud'] else (ratio[0] if 2 in place['cloud'] else ratio[1]))/((run_all_time - (res['times']['1']+res['times']['2']+res['times']['3']))/2)

  ar_url = 'http://%s/controller/add_result'%calc_addr['edge']
  flag = False
  while not flag:
    try:
      requests.post(ar_url, data=result)
      flag = True
    except Exception as e:
      print(e)
  #''' 

  result['place'] = place
  result['think_time'] = think_time
  result['run_time'] = run_all_time
  return result

def do_exis(file_name, url):
  img, data_size = open_file(file_name)
  start = time.perf_counter()
  res_j = requests.get('http://%s/controller/repro'%url)
  calc_addr = json.loads(res_j.text)
  context = getCECInfo(calc_addr)
  context['data_size'] = data_size
  collect_time = time.perf_counter()
  url = 'http://%s/controller/repro'%url
  result = do_task(url, context, img, data_size)  
  result['collect_time'] = collect_time
  return result

def do_prev(file_name, url):
  img, data_size = open_file(file_name)
  context = {
    'data_size': data_size,
  }
  url = 'http://%s/controller/prev'%url
  result = do_task(url, context, img, data_size)  
  result['collect_time'] = 0.0
  return result

def multi_do_exis(file_name, url, n):
  async def do_async(loop):
    async def do_req(i):
      # print('do %d request'%i)
      res = await loop.run_in_executor(None, do_exis, file_name, url)
      # print('fin %d request'%i)
      return res

    tasks = [ do_req(i) for i in range(n) ]
    return await asyncio.gather(*tasks)

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(do_async(loop))
  return results

def multi_do_prev(file_name, url, n):
  async def do_async(loop):
    async def do_req(i):
      # print('do %d request'%i)
      res = await loop.run_in_executor(None, do_prev, file_name, url)
      # print('fin %d request'%i)
      return res

    tasks = [ do_req(i) for i in range(n) ]
    return await asyncio.gather(*tasks)

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(do_async(loop))
  return results

def multi_process_exis(file_name, url, mn, n):
  processes = []
  for i in range(n):
    processes.append(Process(target=multi_do_exis, args=(file_name, url, mn)))
    processes[i].start()
    time.sleep(1)

  for i in range(n):
    processes[i].join()
    print('fin async %d'%i)
 
def multi_process_prev(file_name, url, mn, n):
  processes = []
  for i in range(n):
    processes.append(Process(target=multi_do_prev, args=(file_name, url, mn)))
    processes[i].start()
    time.sleep(1)

  for i in range(n):
    processes[i].join()
    print('fin async %d'%i)

def many_multi_access(file_name, url, mn, n):
  results = []
  for i in range(n):
    result = multi_do_prev(file_name, url, mn) 
    results.append(result)
    #time.sleep(1)
  print(result)


def client_test_exis(file_name, url, n):
  results = []
  for i in range(n):
    #result = multi_do_exis(file_name, url, 1)
    #results.append(result)
    result = do_exis(file_name, url)
    results.append(result)
    time.sleep(0.5)

  book = openpyxl.Workbook()
  sheet = book.active
  sheet.title = 'alg=exis, n=%s'%n
  row_num = 1
  row = sheet['a1':'s1']
  row[0][0].value = 'client_id'
  row[0][1].value = 'alg'
  row[0][2].value = 'ip_addr'
  row[0][3].value = 'pre'
  row[0][4].value = 'result'
  row[0][5].value = 'collect_time'
  row[0][6].value = 'think_time'
  row[0][7].value = 'run_time'
  row[0][8].value = 'input_name'
  row[0][9].value = 'input_size'
  row[0][10].value = 'ans'
  row[0][11].value = 'confidence'
  row[0][12].value = 'pre_task1'
  row[0][13].value = 'pre_task2'
  row[0][14].value = 'pre_task3'
  row[0][15].value = 'res_task1'
  row[0][16].value = 'res_task2'
  row[0][17].value = 'res_task3'
  row[0][18].value = 'place'

  for result in results:
    row_num += 1
    row = sheet[('a'+str(row_num)):('s'+str(row_num))] # 19個
    row[0][0].value = result['client_id']
    row[0][1].value = result['alg']
    row[0][2].value = result['ip_addr']
    row[0][3].value = result['pre']
    row[0][4].value = result['result']
    row[0][5].value = result['collect_time']
    row[0][6].value = result['think_time']
    row[0][7].value = result['run_time']
    row[0][8].value = result['input_name']
    row[0][9].value = result['input_size']
    row[0][10].value = result['ans']
    row[0][11].value = result['confidence']
    row[0][12].value = result['pre_task1']
    row[0][13].value = result['pre_task2']
    row[0][14].value = result['pre_task3']
    row[0][15].value = result['res_task1']
    row[0][16].value = result['res_task2']
    row[0][17].value = result['res_task3']
    row[0][18].value = str(result['place'])

  date = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
  book.save('result_exis_'+date+'.xlsx')


def client_test_prev(file_name, url, n):
  results = []
  for i in range(n):
    #result = multi_do_prev(file_name, url, 1)
    #results.append(result)
    result = do_prev(file_name, url)
    results.append(result)
    time.sleep(0.5)

  book = openpyxl.Workbook()
  sheet = book.active
  sheet.title = 'alg=prev, n=%s'%n
  row_num = 1
  row = sheet['a1':'s1']
  row[0][0].value = 'client_id'
  row[0][1].value = 'alg'
  row[0][2].value = 'ip_addr'
  row[0][3].value = 'pre'
  row[0][4].value = 'result'
  row[0][5].value = 'collect_time'
  row[0][6].value = 'think_time'
  row[0][7].value = 'run_time'
  row[0][8].value = 'input_name'
  row[0][9].value = 'input_size'
  row[0][10].value = 'ans'
  row[0][11].value = 'confidence'
  row[0][12].value = 'pre_task1'
  row[0][13].value = 'pre_task2'
  row[0][14].value = 'pre_task3'
  row[0][15].value = 'res_task1'
  row[0][16].value = 'res_task2'
  row[0][17].value = 'res_task3'
  row[0][18].value = 'place'

  for result in results:
    row_num += 1
    row = sheet[('a'+str(row_num)):('s'+str(row_num))] # 19個
    row[0][0].value = result['client_id']
    row[0][1].value = result['alg']
    row[0][2].value = result['ip_addr']
    row[0][3].value = result['pre']
    row[0][4].value = result['result']
    row[0][5].value = result['collect_time']
    row[0][6].value = result['think_time']
    row[0][7].value = result['run_time']
    row[0][8].value = result['input_name']
    row[0][9].value = result['input_size']
    row[0][10].value = result['ans']
    row[0][11].value = result['confidence']
    row[0][12].value = result['pre_task1']
    row[0][13].value = result['pre_task2']
    row[0][14].value = result['pre_task3']
    row[0][15].value = result['res_task1']
    row[0][16].value = result['res_task2']
    row[0][17].value = result['res_task3']
    row[0][18].value = str(result['place'])

  date = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
  book.save('result_prev_'+date+'.xlsx')

