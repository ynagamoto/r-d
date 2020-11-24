import requests
import json
from faceIdentify.scripts.converter import b2i,i2f,f2i,i2b

'''
url と image の binary を受け取って
get face のリクエストを実行し
image の binary を返すメソッド
'''
def doGetFace(url, img_b):
  # do request 
  res_j = requests.post(url, {'img': img_b})
  res = json.loads(res_j.text)

  # return image binary
  return res['img']

'''
url と image の binary を受け取って
prep image のリクエストを実行し
image の binary を返すメソッド
'''
def doPrepImage(url, img_b):
  # do request 
  res_j = requests.post(url, {'img': img_b})
  res = json.loads(res_j.text)

  # return image binary
  return res['img']

'''
url と image の binary を受け取って
face matching のリクエストを実行し
結果を入れた context を返すメソッド
'''
def doFaceMatching(url, img_b):
  # do request 
  res_j = requests.post(url, {'img': img_b})
  res = json.loads(res_j.text)
  
  context = {
    'label': res['label'],
    'confidence': res['confidence'],
  }

  # return image binary
  return context

