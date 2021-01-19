import requests
import cv2
import json
import base64
from multiprocessing import Process,Value
import os
import time
import socket
import asyncio

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
  data_size = len(img_b) * 8 / 1000000
  return img, data_size

# 実行先をedgeに聞いて実行 -> 結果送信
def do_task(context):
  res_j = requests.post(url, data=context)
  res = json.loads(res_j.text)
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
      next_url = res['calc_addr'][calc]

  context = {
    'client_id': res['client_id'],
    'task_id': str(task+1),
    'data': i2b(img),
    'times': json.dumps(times, ensure_ascii=False, indent=2).encode('utf-8'),
  }

  place = res['place']
  start = time.perf_counter()
  res_j = requests.post('http://{}/calculator/do_task'.format(next_url), data=context)
  run_time = time.perf_counter() - start
  res = json.loads(res_j.text) 

  result = {
    'client_id': res['client_id'],
    'alg': 'test',
    'ip_addr': '0.0.0.0',
    'pre': 0.00,
    'result': run_time,
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

  # 転送時間の計算
  ratio = [0.45397, 0.39966]
  for calc in place:
    for task in place[calc]:
      result['task'+str(task)+'_calc'] = calc
      result['task'+str(task)] = res['times'][str(task)]
  if (len(place['edge']) != 0) and (len(place['cloud']) != 0):
    print('c-e-c')
    result['calc'] = 'c-e-c'
    result['e-c'] = res['times']['edge'+str(place['edge'][0])]
    for calc in ['edge', 'cloud']:
      for task in place[calc]:
        result['e-c'] -= res['times'][str(task)]
    result['e-c'] = data_size*(ratio[0] if 2 in place['cloud'] else ratio[0]*ratio[1])/(result['e-c']/2)
    result['c-e'] = data_size*(1 if 1 in place['edge'] else ratio[0])/((run_time - (res['times']['1']+res['times']['2']+res['times']['3']) - 2*result['e-c'])/2)
    result['c-c'] = result['c-e']+result['e-c']
  elif (len(place['edge']) != 0) and (len(place['cloud']) == 0):
    print('c-e')
    result['calc'] = 'c-e'
    result['c-e'] = data_size*(1 if 1 in place['edge'] else (ratio[0] if 2 in place['edge'] else ratio[1]))/((run_time - (res['times']['1']+res['times']['2']+res['times']['3']))/2)
  elif (len(place['cloud']) != 0) and (len(place['edge']) == 0):
    print('c-c')
    result['calc'] = 'c-c'
    result['c-c'] = data_size*(1 if 1 in place['cloud'] else (ratio[0] if 2 in place['cloud'] else ratio[1]))/((run_time - (res['times']['1']+res['times']['2']+res['times']['3']))/2)

  ar_url = 'http://{}/controller/add_result'%res['calc_addr']['edge']
  requests.post(ar_url, data=result)
  return result

def do_exis(file_name, url):
  img, data_size = open_file(file_name)
  res_j = requests.get(url)
  calc_addr = json.loads(res_j.text)
  context = getCECInfo(calc_addr)
  context['data_size'] = data_size
  result = do_task(context)  
  print(result)

def do_prev(file_name, url):
  img, data_size = open_file(file_name)
  context['data_size'] = data_size
  result = do_task(context)  
  print(result)

def multi_do_exis(file_name, url, n):
  async def do_async(loop):
    async def do_req(i):
      #print('do %d request'%i)
      res = await loop.run_in_executor(None, do_exis, (file_name, url))
      return res

    tasks = [ do_req(i) for i in range(n) ]
    return await asyncio.gather(*tasks)

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(do_async(loop))
  print(results)

def multi_do_prev(file_name, url, n):
  async def do_async(loop):
    async def do_req(i):
      #print('do %d request'%i)
      res = await loop.run_in_executor(None, do_prev, (file_name, url))
      return res

    tasks = [ do_req(i) for i in range(n) ]
    return await asyncio.gather(*tasks)

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(do_async(loop))
  print(results)

def multi_process_access(file_name, url, multi_n, process_n):
  for i in range(process_n):
    processes.apend(Process(target=multi_do_prev, args=(file_name, url, multi_n)))
    processes[i].start()
    time.sleep(1)

  for i in range(process_n):
    processes[i].join()
    
