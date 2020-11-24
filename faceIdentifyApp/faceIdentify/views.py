from django.shortcuts import render
from django.http import HttpResponse
from django.views import View

import requests
import json

from faceIdentify.scripts.converter import f2i,b2i,b2g,i2f,i2b
from faceIdentify.scripts.get_face import get_face
from faceIdentify.scripts.prep_image import prep
from faceIdentify.scripts.face_matching import face_matching

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.
def index(request):
  url = 'http://localhost:8000/calculator/info'
  # url = 'http://172.25.44.94/calculator/info'
  resj = requests.get(url)
  res = json.loads(resj.text)
  return HttpResponse(resj.text)

class FaceIdentify(View):
  def get(self, request, *args, **kwargs):
    context = {
      'title': 'face identify app',
      'msg1': '画像を選択して下さい',
    }
    return render(request, 'faceIdentify/faceIdentify.html', context)

class SelectPlace(View):
  def get(self, request, *args, **kwargs):
    context = {
      'title': 'face identify app',
      'msg1': '画像を選択して下さい',
    }
    return render(request, 'faceIdentify/select_place.html', context)



class GetFace(View):
  def get(self, request, *args, **kwargs):
    return HttpResponse("Please send a face image using the post method.")
    
  def post(self, request, *args, **kwargs):
    img_b = request.POST['img'] 
    img = b2i(img_b)
    face = get_face(img) 
    res_b = i2b(face)
    context = {
      'img': res_b,
    }
    res_j = json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8')
    return HttpResponse(res_j)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(GetFace, self).dispatch(*args, **kwargs)


class PrepImage(View):
  def get(self, request, *args, **kwargs):
    return HttpResponse("Please send a face image using the post method.")
  
  def post(self, request, *args, **kwargs):
    img_b = request.POST['img']
    img = b2i(img_b)
    img_p = prep(img)
    res_b = i2b(img_p)
    context = {
      'img': res_b,
    }
    res_j = json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8')
    return HttpResponse(res_j)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(PrepImage, self).dispatch(*args, **kwargs)


class FaceMatching(View):
  def get(self, request, *args, **kwargs):
    return HttpResponse("Please send a face image using the post method.")

  def post(self, request, *args, **kwargs):
    img_b = request.POST['img']
    img = b2g(img_b)
    label, confidence = face_matching(img)
    context = {
      'label': label,
      'confidence': confidence,
    }
    res_j = json.dumps(context, ensure_ascii=False, indent=2).encode('utf-8')
    return HttpResponse(res_j)

  @method_decorator(csrf_exempt)
  def dispatch(self, *args, **kwargs):
    return super(FaceMatching, self).dispatch(*args, **kwargs)



faceIdentify = FaceIdentify.as_view()
getFace = GetFace.as_view()
prepImage = PrepImage.as_view()
faceMatching = FaceMatching.as_view()
selectPlace = SelectPlace.as_view()
