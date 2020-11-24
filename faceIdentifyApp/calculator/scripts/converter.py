import cv2
import numpy as np
from PIL import Image
import base64

import io
from django.core.files.uploadedfile import InMemoryUploadedFile

def f2b(img_f):
  img_b = base64.b64encode(img_f.read()).decode('utf-8')
  return img_b

def f2i(img_f):
  img_b = f2b(img_f)
  img_array = b2i(img_b)
  return img_array

def i2f(img_a):
  img = Image.fromarray(np.uint8(img_a))
  img_bio = io.BytesIO()
  img.save(img_bio, format='PNG') 
  fsize = img_bio.getbuffer().nbytes
  img_file = InMemoryUploadedFile(img_bio, None, 'test.png', 'image/png', fsize, None)
  return img_f

def i2b(img_a):
  _, encimg = cv2.imencode(".png", img_a)
  img_str = encimg.tostring()
  img_b = base64.b64encode(img_str).decode("utf-8")
  return img_b

def b2i(img_b):
  decimg = base64.b64decode(img_b)
  data_np = np.fromstring(decimg, dtype='uint8')
  img_a = cv2.imdecode(data_np, flags=cv2.IMREAD_COLOR) 
  return img_a

def b2g(img_b):
  decimg = base64.b64decode(img_b)
  data_np = np.fromstring(decimg, dtype='uint8')
  img_a = cv2.imdecode(data_np, flags=cv2.IMREAD_GRAYSCALE) 
  return img_a

