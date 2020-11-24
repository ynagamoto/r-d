import cv2

# Haar-like
cascade_path = '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)

def get_face(image):
  faces = face_cascade.detectMultiScale(image)
  face = faces[0]

  # 顔をリサイズ x, y, w, h
  roi = cv2.resize(image[face[1]:face[1]+face[3], face[0]:face[0]+face[2]], (200, 200), interpolation=cv2.INTER_LINEAR)

  return roi
