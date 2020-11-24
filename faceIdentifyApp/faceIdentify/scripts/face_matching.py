import cv2, os
import numpy as np
from PIL import Image

def face_matching(image):
  # 学習したYAMLファイル
  dir_path = '/home/munvei/workspace/django/faceIdentifyApp/faceIdentify/scripts/'
  trainer_path = 'trainer.yaml'

  # YAMLファイルの読み込み
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.read(os.path.join(dir_path, trainer_path))

  # テスト画像に対して予測実施
  label, confidence = recognizer.predict(image)
  
  # 予測結果を返す
  return label, confidence

