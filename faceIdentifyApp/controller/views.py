from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views import View
from .models import CalcInfo,PrevInfo,Result
from .forms import CalcInfoForm,PrevInfoForm,ResultForm

import requests
import json
#import threading
from multiprocessing import Process,Value,Array
import sys

from faceIdentify.scripts.converter import f2b
from controller.scripts.get_info import getECInfo,getECInfo2

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.

# 各計算資源の情報を集める
class GatherCalcInfo(View):
  def get(self, request, *args, **kwargs):
    edge = CalcInfo.objects.get(name='edge')
    cloud = CalcInfo.objects.get(name='cloud')
    context = {
      'edge': edge.ip_addr,
      'cloud': cloud.ip_addr,
    }
    return HttpResponse(json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8'))

  def post(self, request, *args, **kwargs):
    # session id を取得
    request.session.create()
    client_id = request.session.session_key

    # 実行場所
    edge_info = CalcInfo.objects.get(name='edge') 
    cloud_info = CalcInfo.objects.get(name='cloud')  
    edge = 'http://' + edge_info.ip_addr
    cloud = 'http://' + cloud_info.ip_addr
    cloud_local = 'http://' + cloud_info.local_addr
    add_task = 'calculator/add_task'
    do_task = 'calculator/do_task'
    
    ec_info = getECInfo({'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr})

    # cpu usage, iperf, ping のデータをjsonで返す
    context = {
      'client': {
        'cpu': float(request.POST['cpu']),
        'to edge': {
          'bw': float(request.POST['edge_bw']),
      'ping': float(request.POST['edge_ping']),
        },
        'to cloud': {
          'bw': float(request.POST['cloud_bw']),
          'ping': float(request.POST['cloud_ping']),
        },
      },
      'edge': {
        'cpu': ec_info['edge']['cpu'], 
        'to edge': {
          'bw': ec_info['edge']['bw'],
          'ping': ec_info['edge']['ping'],
        },

        'to cloud': {
          'bw': ec_info['cloud']['bw'],
          'ping': ec_info['cloud']['ping'],
        },
      },
      'cloud': {
        'cpu': ec_info['cloud']['cpu'], 
      },
    }
    return HttpResponse(json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8'))

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(GatherCalcInfo, self).dispatch(*args, **kwargs)

class ReproduceExisting(View):
  def get(self, request, *args, **kwargs):
    edge = CalcInfo.objects.get(name='edge')
    cloud = CalcInfo.objects.get(name='cloud')
    context = {
      'edge': edge.ip_addr,
      'cloud': cloud.ip_addr,
    }
    return HttpResponse(json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8'))

  def post(self, request, *args, **kwargs):
    # 実行場所
    edge_info = CalcInfo.objects.get(name='edge') 
    cloud_info = CalcInfo.objects.get(name='cloud')  
    edge = 'http://' + edge_info.ip_addr
    edge_local = 'http://' + edge_info.local_addr
    cloud = 'http://' + cloud_info.ip_addr
    cloud_local = 'http://' + cloud_info.local_addr
    add_task = '/calculator/add_task'
    do_task = '/calculator/do_task'
    urls = {'edge': edge, 'edge_local': edge_local, 'cloud': cloud, 'cloud_local': cloud_local}
    calc_addr = {'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr}
    
    # 集める
    # ec_info = getECInfo({'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr})
    ec_info = getECInfo2({'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr})

    info = {
      'client': {
        'cpu': float(request.POST['cpu']),
        'to edge': {
          'bw': float(request.POST['edge_bw']),
          'ping': float(request.POST['edge_ping']),
        },
        'to cloud': {
          'bw': float(request.POST['cloud_bw']),
          'ping': float(request.POST['cloud_ping']),
        },
      },
      'edge': {
        'cpu': float(ec_info['edge']['cpu']), 
        'to edge': {
          'bw': float(ec_info['edge']['bw']),
          'ping': float(ec_info['edge']['ping']),
        },
        'to cloud': {
          'bw': float(ec_info['cloud']['bw']),
          'ping': float(ec_info['cloud']['ping']),
        },
      },
      'cloud': {
        'cpu': float(ec_info['cloud']['cpu']), 
      },
    }
    print(info)

    # session id を取得
    request.session.create()
    client_id = request.session.session_key
    data_size = float(request.POST['data_size'])
    task_info = {
      'client_id': client_id,
      'task_id': '',
      'next_task': '',
      'next_url': '',
    }

    ''' 配置先を決めるアルゴリズム '''
    ratio = [0.45397, 0.39966]
    # 計算時間の推定
    tasks = {
      'num': 3,
      'client': [ 0.08490503, 0.00444955, 1000 ],
      'edge': [0.02271162, 0.00190227, 1.93171145 ],
      'cloud': [0.02198952, 0.00155184, 1.68139666 ],
    }
    run_times = {'client': [0]*tasks['num'], 'edge': [0]*tasks['num'], 'cloud': [0]*tasks['num']}
    for calc in ['client', 'edge', 'cloud']:
      for i in range(tasks['num']):
        if calc == 'client' and i == tasks['num']-1: continue
        temp = 1 if i == 0 else (ratio[0] if i == 1 else ratio[0]*ratio[1])
        cpu = 100.0-info[calc]['cpu']
        run_times[calc][i] = (tasks[calc][i]*data_size*temp) / (cpu/100 if cpu != 0.0 else 0.00001/100) 

    # 転送時間の推定 
    trans_times = {'client': {'edge': [0]*tasks['num'], 'cloud': [0]*tasks['num']}, 'edge': {'cloud': [0]*tasks['num']}}
    for calc in ['edge', 'cloud']:
      for i in range(tasks['num']): 
        temp = 1 if i == 0 else (ratio[0] if i == 1 else ratio[0]*ratio[1])
        trans_times['client'][calc][i] = (data_size*temp/info['client']['to '+calc]['bw']) + info['client']['to '+calc]['ping']/1000 # client
        if calc != 'edge':
          trans_times['edge'][calc][i] = (data_size*temp/info['edge']['to '+calc]['bw']) + info['edge']['to '+calc]['ping']/1000 # edge

    # 最も短いものを求める
    est_time = 100000.0
    place = {'client': [], 'edge': [], 'cloud': []}
    time_client = 0.0
    task_client = []
    for i in range(tasks['num']): # client
      if i != 0:
        task_client.append(i)
        time_client += run_times['client'][i-1]
      #print("client: %d" % i)
      #print('time_client: %f' % (time_client))
      
      time_edge = 0.0
      task_edge = []
      for j in range(tasks['num']+1): # edge
        if j != 0 and j <= i: continue
        time_edge += trans_times['client']['edge'][i] if j != 0 else 0.0
        if j != 0: 
          task_edge.append(j)
          time_edge += run_times['edge'][j-1]
        #print("  edge: %d" % j)
        #print('  time_edge: %f' % (time_edge))

        time_cloud = 0.0
        task_cloud = []
        for k in range(tasks['num']+1): # cloud
          if not((j == tasks['num'] and k == 0) or (i < k and j < k and j != tasks['num'])): continue
          time_cloud += 0.0 if k == 0 else (trans_times['client']['cloud'][i] if j == 0 else trans_times['edge']['cloud'][j])
          if k != 0: 
            task_cloud.append(k)
            time_cloud += run_times['cloud'][k-1]
          #print("    cloud: %d" % k)
          #print('    time_cloud: %f' % (time_cloud))

        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}".format(time_client, time_edge, time_cloud))
        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}\n".format(task_client, task_edge, task_cloud))
        temp_t = time_client + time_edge + time_cloud
        #print('判定')
        if est_time > temp_t:
          est_time = temp_t
          place['client'] = task_client[:]
          place['edge'] = task_edge[:]
          place['cloud'] = task_cloud[:]

    # タスクの配置
    def send_task(url, task_info):
      res = requests.post(url, data=task_info)
    
    processes = []
    for calc in ['edge', 'cloud']:   
      for i in place[calc]:
        task_info['task_id'] = str(i)
        task_info['next_task'] = str(i+1) if i < tasks['num'] else str(0) 
        if task_info['next_task'] != '0':
          for hoge in ['edge', 'cloud']:
            if i+1 in place[hoge]: task_info['next_url'] = (urls[hoge] if calc != hoge else urls[hoge+'_local'])
        else:
          task_info['next_url'] = 'client'

        url = urls[calc]+add_task
        process = Process(target=send_task, args=(url, task_info))
        process.start()
        processes.append(process)
    for process in processes:
      process.join()

    return HttpResponse(json.dumps({'client_id': client_id, 'est_time': est_time, 'place': place, 'calc_addr': calc_addr}, ensure_ascii=False, indent=2).encode('utf-8'))

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(ReproduceExisting, self).dispatch(*args, **kwargs)

class UsePrevInfo(View):
  def get(self, request, *args, **kwargs):
    edge = CalcInfo.objects.get(name='edge')
    cloud = CalcInfo.objects.get(name='cloud')
    context = {
      'edge': edge.ip_addr,
      'cloud': cloud.ip_addr,
    }
    return HttpResponse(json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8'))

  def post(self, request, *args, **kwargs):
    # 実行場所
    edge_info = CalcInfo.objects.get(name='edge') 
    cloud_info = CalcInfo.objects.get(name='cloud')  
    edge = 'http://' + edge_info.ip_addr
    edge_local = 'http://' + edge_info.local_addr
    cloud = 'http://' + cloud_info.ip_addr
    cloud_local = 'http://' + cloud_info.local_addr
    add_task = '/calculator/add_task'
    do_task = '/calculator/do_task'
    urls = {'edge': edge, 'edge_local': edge_local, 'cloud': cloud, 'cloud_local': cloud_local}
    calc_addr = {'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr}
    
    # session id を取得
    request.session.create()
    client_id = request.session.session_key
    data_size = float(request.POST['data_size'])
    task_info = {
      'client_id': client_id,
      'task_id': '',
      'next_task': '',
      'next_url': '',
    }

    # 計算時間の推定
    tasks = {
      'num': 3,
    }
    info = PrevInfo.objects.get(prev_id=0)

    # 転送時間の推定 
    trans_times = {'client': {'edge': [0]*tasks['num'], 'cloud': [0]*tasks['num']}, 'edge': {'cloud': [0]*tasks['num']}}
    ratio = [0.45397, 0.39966]
    for calc in ['edge', 'cloud']:
      for i in range(tasks['num']): 
        temp = 1 if i == 0 else (ratio[0] if i == 1 else ratio[0]*ratio[1])
        trans_times['client'][calc][i] = (data_size*temp/getattr(info, 'client_'+calc)) # client to edge or client
        if calc != 'edge':
          trans_times['edge'][calc][i] = (data_size*temp/getattr(info, 'edge_'+calc)) # edge to cloud

    ''' 配置先を決めるアルゴリズム ''' 
    # 最も短いものを求める
    est_time = 100000.0
    place = {'client': [], 'edge': [], 'cloud': []}
    time_client = 0.0
    task_client = []
    for i in range(tasks['num']): # client
      temp = 1 if i == 0 else (ratio[0] if i == 1 else ratio[0]*ratio[1])
      if i != 0:
        task_client.append(i)
        time_client += getattr(info, 'client_task'+str(i)) * data_size * temp
      #print("client: %d" % i)
      #print('time_client: %f' % (time_client))
      
      time_edge = 0.0
      task_edge = []
      for j in range(tasks['num']+1): # edge
        if j != 0 and j <= i: continue
        time_edge += trans_times['client']['edge'][i] if j != 0 else 0.0
        if j != 0: 
          task_edge.append(j)
          time_edge += getattr(info, 'edge_task'+str(j)) * data_size * temp
        #print("  edge: %d" % j)
        #print('  time_edge: %f' % (time_edge))

        time_cloud = 0.0
        task_cloud = []
        for k in range(tasks['num']+1): # cloud
          if not((j == tasks['num'] and k == 0) or (i < k and j < k and j != tasks['num'])): continue
          time_cloud += 0.0 if k == 0 else (trans_times['client']['cloud'][i] if j == 0 else trans_times['edge']['cloud'][j])
          if k != 0: 
            task_cloud.append(k)
            time_cloud += getattr(info, 'cloud_task'+str(k)) * data_size * temp
          #print("    cloud: %d" % k)
          #print('    time_cloud: %f' % (time_cloud))

        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}".format(time_client, time_edge, time_cloud))
        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}\n".format(task_client, task_edge, task_cloud))
        temp_t = time_client + time_edge + time_cloud
        #print('判定')
        if est_time > temp_t:
          est_time = temp_t
          place['client'] = task_client[:]
          place['edge'] = task_edge[:]
          place['cloud'] = task_cloud[:]

    # タスクの配置
    def send_task(url, task_info):
      res = requests.post(url, data=task_info)
    
    processes = []
    for calc in ['edge', 'cloud']:   
      for i in place[calc]:
        task_info['task_id'] = str(i)
        task_info['next_task'] = str(i+1) if i < tasks['num'] else str(0) 
        if task_info['next_task'] != '0':
          for hoge in ['edge', 'cloud']:
            if i+1 in place[hoge]: task_info['next_url'] = (urls[hoge] if calc != hoge else urls[hoge+'_local'])
        else:
          task_info['next_url'] = 'client'

        url = urls[calc]+add_task
        process = Process(target=send_task, args=(url, task_info))
        process.start()
        processes.append(process)
    for process in processes:
      process.join()

    return HttpResponse(json.dumps({'client_id': client_id, 'est_time': est_time, 'place': place, 'calc_addr': calc_addr}, ensure_ascii=False, indent=2).encode('utf-8'))

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(UsePrevInfo, self).dispatch(*args, **kwargs)


class TestPlace(View):
  def get(self, request, *args, **kwargs):
    context = {
      'title': 'test place',
      'msg1': 'test place で face identify を実行します',
    }

    return render(request, 'controller/face_identify.html', context)

  def post(self, request, *args, **kwargs):
    # session id を取得
    request.session.create()
    client_id = request.session.session_key

    # 実行場所
    edge_info = CalcInfo.objects.get(name='edge') 
    cloud_info = CalcInfo.objects.get(name='cloud')  
    edge = 'http://' + edge_info.ip_addr
    edge_local = 'http://' + edge_info.local_addr
    cloud = 'http://' + cloud_info.ip_addr
    cloud_local = 'http://' + cloud_info.local_addr
    add_task = '/calculator/add_task'
    do_task = '/calculator/do_task'
    urls = {'edge': edge, 'edge_local': edge_local, 'cloud': cloud, 'cloud_local': cloud_local}
    
    # タスクの配置
    tasks = {}
    tasks['num'] = 3
    def send_task(url, task_info):
      res = requests.post(url, data=task_info)
    
    place = json.loads(request.POST['place'])
    print(place)
    processes = []
    for calc in ['edge', 'cloud']:   
      for i in place[calc]:
        task_info = {
          'client_id': client_id,
          'task_id': '',
          'next_task': '',
          'next_url': '',
        }
        task_info['task_id'] = str(i)
        task_info['next_task'] = str(i+1) if i < tasks['num'] else str(0) 
        if task_info['next_task'] != '0':
          for hoge in ['edge', 'cloud']:
            if i+1 in place[hoge]: task_info['next_url'] = (urls[hoge] if hoge != 'cloud' else urls['cloud_local'])
        else:
          task_info['next_url'] = 'client'

        url = urls[calc]+add_task
        process = Process(target=send_task, args=(url, task_info))
        process.start()
        processes.append(process)
    for process in processes:
      process.join()
    
    context = {
      'data': request.POST['data'],
      'client_id': client_id,
      'task_id': '1',
      'times': '{}',
    }
    #return HttpResponse(context['client_id'])
    res = requests.post('http://%s/calculator/do_task'%cloud_info.ip_addr, data=context)

    return HttpResponse(res)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(TestPlace, self).dispatch(*args, **kwargs)

def showCalcInfo(request):
  edge = CalcInfo.objects.get(name='edge') 
  cloud = CalcInfo.objects.get(name='cloud') 
  context = {
    'title': 'show calc info',
    'edge': edge,
    'cloud': cloud,
  }
  return render(request, 'controller/show_calc_info.html', context)

def editCalcInfo(request, id):
  calc_info = CalcInfo.objects.get(id=id)
  if request.method == 'POST':
    calc_info = CalcInfoForm(request.POST, instance=calc_info)
    calc_info.save()
    return redirect(to='/controller/show_calc_info')
  
  context = {
    'title': 'edit calc info',
    'id': id,
    'form': CalcInfoForm(instance=calc_info)
  }
  return render(request, 'controller/edit_calc_info.html', context)


def showPrevInfo(request):
  prev_info = PrevInfo.objects.all()
  context = {
    'title': 'show prev info',
    'data': prev_info,
  }
  return render(request, 'controller/show_prev_info.html', context)

@csrf_exempt
def editPrevInfo(request):
  prev_info = PrevInfo.object.get(prev_id=0)
  if request.method == 'POST':
    prev_info = PrevFrom(request.POST, instance=prev_info)
    prev_info.save()
    return redirect(to='showPrevInfo')

  context = {
    'title': 'edit prev info',
    'form': prev_info,
  }
  return render(request, 'controller/edit_prev_info.html', context)

def showResult(request):
  results = Result.objects.all()
  context = {
    'title': 'show result',
    'data': results,
  }
  return render(request, 'controller/show_result.html', context)

@csrf_exempt
def addResult(request):
  tasks = 3
  if request.method == 'POST':
    form = ResultForm(request.POST, instance=Result())
    form.save()
    result = Result.objects.get(client_id=request.POST['client_id'])
    result.ip_addr = request.META.get('REMOTE_ADDR')
    result.save()

    prev_info = PrevInfo.objects.get(prev_id=0)
    prev_info.latest_id = request.POST['client_id'] 
    prev_info.latest_addr = request.META.get('REMOTE_ADDR')
    for task in range(1, tasks+1): 
      setattr(prev_info, request.POST['task'+str(task)+'_calc']+'_task'+str(task), request.POST['task'+str(task)])

    if request.POST['calc'] == 'c-e':
      prev_info.client_edge = request.POST['c-e']
    elif request.POST['calc'] == 'c-c':
      prev_info.client_cloud = request.POST['c-c']
    elif request.POST['calc'] == 'c-e-c':
      prev_info.client_edge = request.POST['c-e']
      prev_info.edge_cloud = request.POST['e-c']
      prev_info.client_cloud = request.POST['c-c']
    prev_info.save()

    return HttpResponse("ok")
    #return redirect(to='showResult')

  context = {
    'title': 'add result',
    'form': ResultForm(),
  }
  return render(request, 'controller/add_result.html', context)
  

info = GatherCalcInfo.as_view()
repro = ReproduceExisting.as_view()
prev = UsePrevInfo.as_view()
testPlace = TestPlace.as_view()

