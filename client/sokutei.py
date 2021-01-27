import requests
import cv2
import json
import base64
from multiprocessing import Process,Value
#import threading
import os
import time

# from bs4 import BeautifulSoup
from get_info import getCECInfo
from converter import i2b
from tasks import get_face,prep_img,face_matching

file_name = 'pic/test01.png'

# ファイルの読み込み
img = cv2.imread(file_name)
img_b = i2b(img)
data_size = len(img_b) * 8 / 1000000
print("file size: %f" % data_size)

# 実行先を確認して実行
start = float(time.perf_counter())
img = get_face(img)
img_b = i2b(img)
data_size = len(img_b) * 8 / 1000000
print("after get face: %f" % data_size)
print("run time (get face): %f" % (time.perf_counter()-start))

start = float(time.perf_counter())
img = prep_img(img)
img_b = i2b(img)
data_size = len(img_b) * 8 / 1000000
print("after prep img: %f" % data_size)
print("run time (prep img): %f" % (time.perf_counter()-start))

start = float(time.perf_counter())
res = face_matching(img)
print("run time (face matching): %f" % (time.perf_counter()-start))
print(res)

