from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views import View

import requests
import json
import threading

from faceIdentify.scripts.converter import f2b
from controller.scripts.controller import getCalcInfo

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.

# 各計算資源の情報を集める
def controller(request):
  # edge
  edge = 'http://localhost:8000/calculator/info'
  # cloud
  # cloud = ''

  results = {}
  edge = threading.Thread(target=getCalcInfo, args=('edge', edge, results))

  edge.start()
  edge.join()

  res_j = json.dumps(results, ensure_ascii=False, indent=2).encode('utf-8')
  return HttpResponse(res_j) 

class TestPlace(View):
  def get(self, request, *args, **kwargs):
    context = {
      'title': 'test place',
      'msg1': 'test place で face identify を実行します',
    }

    return render(request, 'controller/face_identify.html', context)

  def post(self, request, *args, **kwargs):
    # session id を取得
    client_id = '1'

    # 実行場所
    edge = 'http://172.21.34.203/'
    add_task = 'calculator/add_task'
    do_task = 'calculator/do_task'

    # ファイルの変換
    img_b = f2b(request.FILES['img'])
    
    task_info = {
      'client_id': client_id,
      'task_id': '',
      'next_task': '',
      'next_url': '',
    }

    max = 3
    for i in range(3):
      task_info['task_id'] = str(i+1)
      task_info['next_task'] = str(i+2) if i != (max-1) else '0'
      task_info['next_url'] = edge
      requests.post(edge+add_task, data=task_info)

    # 実行
    res_j = requests.post(edge+do_task, data={'client_id': client_id, 'task_id': '1', 'data': img_b})
    return HttpResponse(res_j)
    res = json.loads(res_j.text)

    context = {
      'title': 'Result',
      'label': res['label'],
      'confidence': res['confidence'],
    }
    return render(request, 'faceIdentify/result.html', context)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(TestPlace, self).dispatch(*args, **kwargs)

class TestClient(View):
  def get(self, request, *args, **kwargs):
    context = {
      'title': 'test client',
      'msg1': 'test client で face identify を実行します',
    }

    return render(request, 'controller/face_identify.html', context)

  def post(self, request, *args, **kwargs):
    # session id を取得
    client_id = '1' 
    # 実行場所
    add_task = 'http://localhost:8000/calculator/add_task'
    do_task = 'http://localhost:8000/calculator/do_task'

    # ファイルの変換
    img_b = f2b(request.FILES['img'])
    
    task_info = {
      'client_id': client_id,
      'task_id': '',
      'next_task': '',
      'next_url': '',
    }

    task_info['task_id'] = '3'
    task_info['next_task'] = '0'
    task_info['next_url'] = 'localhost:8000'
    requests.post(add_task, data=task_info)

    # 実行
    res = {
      'client_id': client_id,
      'client_task': 2,
      'next_url': 'localhost:8000'
    }
    res_j = json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8')
    return HttpResponse(res_j)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(TestClient, self).dispatch(*args, **kwargs)



testPlace = TestPlace.as_view()
testClient = TestClient.as_view()
