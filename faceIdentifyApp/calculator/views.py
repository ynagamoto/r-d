from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views import View
import json
import requests
import threading

from calculator.scripts.get_info import getCpuUsage,getNwBw,getNwDelay
import calculator.scripts.server as server
from calculator.scripts.tasks import get_face,prep_img,face_matching

from .models import TaskInfo
from .forms import TaskForm

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.

def index(request):
  return HttpResponse("Hello. This is calc index.")

# CPU使用率，ネットワーク遅延，ネットワーク帯域幅
def info(request):
  # IPアドレス
  caddr = request.META.get('REMOTE_ADDR')
  saddr = server.info()

  info = {
    'caddr': caddr,
    'saddr': saddr,
    'cpu_u': 0.0,
    'nw_b': 0.0,
    'nw_d': 0.0,
  }
  getcu = threading.Thread(target=getCpuUsage, args=(info,)) # CPU使用率
  getnb = threading.Thread(target=getNwBw, args=(caddr, info)) # 帯域幅
  getnd = threading.Thread(target=getNwDelay, args=(caddr, info)) # 遅延

  getcu.start()
  getnb.start()
  getnd.start()
  getcu.join()
  getnb.join()
  getnd.join()
  
  resj = json.dumps(info, ensure_ascii=False, indent=2)
  return HttpResponse(resj)

class DoTask(View):
  def get(self, request, *args, **kwargs):
    return HttpResponse('do task')

  def post(self, request, *args, **kwargs):
    cid, tid = request.POST['client_id'], request.POST['task_id']
    task_info = TaskInfo.objects.get(client_id=cid, task_id=tid)
    task = {
      'client_id': cid,
      'task_id': tid,
      'data': request.POST['data'],
      'next_task': task_info.next_task,
      'next_url': task_info.next_url,
    } 
    task_info.delete()

    data = task['data']
    if task['task_id'] == '1': # get face
      res = get_face(data)
    elif task['task_id'] == '2': # prep image
      res = prep_img(data)
    elif task['task_id'] == '3': # face matching
      res = face_matching(data)

    if task['next_task'] != '0': # next_task が '0' でないならを実行
      url = 'http://{}/calculator/do_task'.format(task['next_url']) 
      context = {
        'client_id': task['client_id'],
        'task_id': task['next_task'],
        'data': res,
      }
      res_j = requests.post(url, data=context)
    else: # next_task が '0' なら最後のタスク
      res_j = res
    return HttpResponse(res_j)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(DoTask, self).dispatch(*args, **kwargs)



def showTask(request):
  if 'client_id' in request.GET:
    cid = request.GET['client_id']
    if 'task_id' in request.GET:
      tid = request.GET['task_id']
      data = TaskInfo.objects.filter(client_id=cid, task_id=tid)
    else:
      data = TaskInfo.objects.filter(client_id=cid)
  else:
    data = TaskInfo.objects.all()

  context = {
    'title': 'show task',
    'msg': 'task list',
    'data': data,
  }
  return render(request, 'calculator/show_task.html', context)

@csrf_exempt
def addTask(request):
  if request.method == 'POST':
    task = TaskForm(request.POST, instance=TaskInfo())
    task.save()
    return redirect(to='showTask')

  context = {
    'title': 'add task',
    'form': TaskForm(),
  } 
  return render(request, 'calculator/add_task.html', context)

def editTask(request, cid, tid):
  task = TaskInfo.objects.get(client_id=cid, task_id=tid)
  if request.method == 'POST':
    if request.POST['submit'] == 'cancel':
      return redirect(to='/calculator/show_task')
    task = TaskForm(request.POST, instance=task)
    task.save()
    return redirect(to='/calculator/show_task')

  context = {
    'title': 'Edit Task',
    'cid': cid,
    'tid': tid,
    'form': TaskForm(instance=task),
  }
  return render(request, 'calculator/edit_task.html', context)

def deleteTask(request, cid, tid):
  task = TaskInfo.objects.get(client_id=cid, task_id=tid)
  if request.method == 'POST':
    if request.POST['submit'] == 'cancel':
      return redirect(to='/calculator/show_task')
    task.delete()
    return redirect(to='/calculator/show_task')

  context = {
    'title': 'Delete Task',
    'cid': cid,
    'tid': tid,
    'form': TaskForm(instance=task)
  }
  return render(request, 'calculator/delete_task.html', context)

def deleteAllTask(request):
  tasks = TaskInfo.objects.all()
  for task in tasks:
    task.delete()
  return redirect(to='/calculator/show_task')


def sendTask(request):
  url = 'http://localhost:8000/calculator/add_task'  
  item = {
    'client_id': '333333',
    'task_id': '1',
    'next_task': '2',
    'next_url': 'edge',
  }
  res = requests.post(url, data=item) 
  return redirect(to='/calculator/show_task')


doTask = DoTask.as_view()

