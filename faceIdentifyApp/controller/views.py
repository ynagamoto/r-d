from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views import View
from .models import CalcInfo
from .forms import CalcInfoForm

import requests
import json
import threading

from faceIdentify.scripts.converter import f2b
from controller.scripts.get_info import getECInfo

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
    
    # 集める
    ec_info = getECInfo({'edge': edge_info.ip_addr, 'cloud': cloud_info.ip_addr})

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
    # 計算時間の推定
    tasks = {
      'num': 3,
      'client': [ 0.2, 0.01, 1000 ],
      'edge': [0.04, 0.005, 0.25 ],
      'cloud': [0.01, 0.005, 0.25 ],
    }
    run_times = {'client': [0]*tasks['num'], 'edge': [0]*tasks['num'], 'cloud': [0]*tasks['num']}
    for calc in ['client', 'edge', 'cloud']:
      for i in range(tasks['num']):
        if calc == 'client' and i == tasks['num']-1: continue
        run_times[calc][i] = (tasks[calc][i]*data_size) / (100.0-info[calc]['cpu']) 

    # 転送時間の推定 
    trans_times = {'client': {'edge': [0]*tasks['num'], 'cloud': [0]*tasks['num']}, 'edge': {'cloud': [0]*tasks['num']}}
    for calc in ['edge', 'cloud']:
      for i in range(tasks['num']): 
        trans_times['client'][calc][i] = (data_size/info['client']['to '+calc]['bw']) + info['client']['to '+calc]['ping']/1000 # client
        if calc != 'edge':
          trans_times['edge'][calc][i] = (data_size/info['edge']['to '+calc]['bw']) + info['edge']['to '+calc]['ping']/1000 # edge

    # 最も短いものを求める
    est_time = 100000.0
    place = {'client': [], 'edge': [], 'cloud': []}
    time_client = 0.0
    task_client = []
    for i in range(tasks['num']): # client
      if i != 0:
        task_client.append(i)
        time_client += run_times['client'][i-1]
      print("client: %d" % i)
      print('time_client: %f' % (time_client))
      
      time_edge = 0.0
      task_edge = []
      for j in range(tasks['num']+1): # edge
        if j != 0 and j <= i: continue
        time_edge += trans_times['client']['edge'][i] if j != 0 else 0.0
        if j != 0: 
          task_edge.append(j)
          time_edge += run_times['edge'][j-1]
        print("  edge: %d" % j)
        print('  time_edge: %f' % (time_edge))

        time_cloud = 0.0
        task_cloud = []
        for k in range(tasks['num']+1): # cloud
          if not((j == tasks['num'] and k == 0) or (i < k and j < k and j != tasks['num'])): continue
          time_cloud += 0.0 if k == 0 else (trans_times['client']['cloud'][i] if j == 0 else trans_times['edge']['cloud'][j])
          if k != 0: 
            task_cloud.append(k)
            time_cloud += run_times['cloud'][k-1]
          print("    cloud: %d" % k)
          print('    time_cloud: %f' % (time_cloud))

        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}".format(time_client, time_edge, time_cloud))
        #print("\'client\': {}, \'edge\': {}, \'cloud\': {}\n".format(task_client, task_edge, task_cloud))
        temp_t = time_client + time_edge + time_cloud
        print('判定')
        if est_time > temp_t:
          est_time = temp_t
          place['client'] = task_client[:]
          place['edge'] = task_edge[:]
          place['cloud'] = task_cloud[:]

    test = {'client': [1, 2], 'edge': [3], 'cloud': []}
    #place = test

    # タスクの配置
    def send_task(url, task_info):
      res = requests.post(url, data=task_info)
    
    threads = []
    for calc in ['edge', 'cloud']:   
      for i in place[calc]:
        task_info['task_id'] = str(i)
        task_info['next_task'] = str(i+1) if i < tasks['num'] else str(0) 
        if task_info['next_task'] != '0':
          for hoge in ['edge', 'cloud']:
            if i+1 in place[hoge]: task_info['next_url'] = urls[hoge]
        else:
          task_info['next_url'] = 'client'

        url = urls[calc]+add_task
        thread = threading.Thread(target=send_task, args=(url, task_info))
        thread.start()
        threads.append(thread)
    for thread in threads:
      thread.join()

    return HttpResponse(json.dumps({'client_id': client_id, 'est_time': est_time, 'place': place}, ensure_ascii=False, indent=2).encode('utf-8'))

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(ReproduceExisting, self).dispatch(*args, **kwargs)



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
    edge = CalcInfo.objects.get(name='edge') 
    cloud = CalcInfo.objects.get(name='cloud') 
 
    edge = 'http://' + edge.ip_addr
    cloud = 'http://' + cloud.ip_addr
    cloud_local = 'http://' + cloud.local_addr
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

    """
    max = 3
    for i in range(3):
      task_info['task_id'] = str(i+1)
      task_info['next_task'] = str(i+2) if i != (max-1) else '0'
      task_info['next_url'] = edge
      requests.post(edge+add_task, data=task_info)
    """

    task_info['task_id'] = '1'
    task_info['next_task'] = '2'
    task_info['next_url'] = cloud
    requests.post(edge+add_task, data=task_info)

    task_info['task_id'] = '2'
    task_info['next_task'] = '3'
    task_info['next_url'] = cloud_local
    requests.post(cloud+add_task, data=task_info)

    task_info['task_id'] = '3'
    task_info['next_task'] = '0'
    task_info['next_url'] = cloud_local
    requests.post(cloud+add_task, data=task_info)

    # 実行
    res_j = requests.post(edge+do_task, data={'client_id': client_id, 'task_id': '1', 'data': img_b})
    return HttpResponse(res_j)
    res = json.loads(res_j.text)
    request.session.flush()

    context = {
      'title': 'Result',
      'label': res['label'],
      'confidence': res['confidence'],
    }
    return render(request, 'faceIdentify/result.html', context)

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

info = GatherCalcInfo.as_view()
repro = ReproduceExisting.as_view()
testPlace = TestPlace.as_view()
