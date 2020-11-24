import cv2

def prep(image):
  gimg = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
  prep_image = cv2.equalizeHist(gimg)
  return prep_image
