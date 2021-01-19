import cv2
import os
import numpy as np
from PIL import Image
import json

from calculator.scripts.converter import b2i,b2g,i2b

# Haar-like
cascade_path = '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)

def get_face(img_b):
  img = b2i(img_b)
  faces = face_cascade.detectMultiScale(img)
  face = faces[0]

  # 顔をリサイズ x, y, w, h
  roi = cv2.resize(img[face[1]:face[1]+face[3], face[0]:face[0]+face[2]], (200, 200), interpolation=cv2.INTER_LINEAR)

  return i2b(roi)

def prep_img(img_b):
  img = b2i(img_b)
  gimg = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
  pimg = cv2.equalizeHist(gimg)
  return i2b(pimg)

def face_matching(img_b):
  # 学習したYAMLファイル
  dir_path = '/home/munvei/workspace/git/r-d/faceIdentifyApp/calculator/scripts/'
  #dir_path = '/root/workspace/git/r-d/faceIdentifyApp/calculator/scripts/'
  #dir_path = '/home/ec2-user/git/r-d/faceIdentifyApp/calculator/scripts/'
  trainer_path = 'trainer.yaml'

  # YAMLファイルの読み込み
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.read(os.path.join(dir_path, trainer_path))

  # テスト画像に対して予測実施
  img = b2g(img_b)
  label, confidence = recognizer.predict(img)
  
  res = {
    'label': label,
    'confidence': confidence,
  }
  res_j = json.dumps(res, ensure_ascii=False, indent=2).encode('utf-8')
  # 予測結果を返す
  return res_j


