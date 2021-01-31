from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.views import View
import json
import requests
import threading
import time

from calculator.scripts.get_cpu_usage import getCpuUsage
from calculator.scripts.tasks import get_face,prep_img,face_matching

from .models import TaskInfo
from .forms import TaskForm

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.

def index(request):
  return HttpResponse("Hello. This is calc index.")

# CPU使用率，ネットワーク遅延，ネットワーク帯域幅
@csrf_exempt
def info(request):
  resj = json.dumps({'cpu': getCpuUsage()}, ensure_ascii=False, indent=2).encode('utf-8')
  return HttpResponse(resj)

class DoTask(View):
  def get(self, request, *args, **kwargs):
    return HttpResponse('do task')

  def post(self, request, *args, **kwargs):
    mycalcname = 'edge'
    start = time.perf_counter()
    cid, tid = request.POST['client_id'], request.POST['task_id']
    task_info = TaskInfo.objects.get(client_id=cid, task_id=tid)
    task = {
      'client_id': cid,
      'task_id': tid,
      'data': request.POST['data'],
      'next_task': task_info.next_task,
      'next_url': task_info.next_url,
    } 
    times = json.loads(request.POST['times'])

    data = task['data']
    if task['task_id'] == '1': # get face
      res = get_face(data)
    elif task['task_id'] == '2': # prep image
      res = prep_img(data)
    elif task['task_id'] == '3': # face matching
      res = face_matching(data)
    task_info.delete()
    times[task['task_id']] = time.perf_counter()-start

    if task['next_task'] != '0': # next_task が '0' でないなら実行
      url = '{}/calculator/do_task'.format(task['next_url']) 
      context = {
        'client_id': task['client_id'],
        'task_id': task['next_task'],
        'data': res,
        'times': json.dumps(times, ensure_ascii=False, indent=2).encode('utf-8'),
      }
      res_j = requests.post(url, data=context)
      res = json.loads(res_j.text)
      res['times'][mycalcname+request.POST['task_id']] = time.perf_counter() - start
      #print(res)
      res_j = json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8')
      return HttpResponse(res_j)
    else: # next_task が '0' なら最後のタスク
      res = json.loads(res)
      res['client_id'] = task['client_id']
      res['times'] = times
      res['times'][mycalcname+request.POST['task_id']] = time.perf_counter() - start
      res_j = json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8')
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
    return HttpResponse('ok')
    #return redirect(to='showTask')

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
      return HttpResponse('ok')
      #return redirect(to='/calculator/show_task')
    task.delete()
    return HttpResponse('ok')
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


doTask = DoTask.as_view()

