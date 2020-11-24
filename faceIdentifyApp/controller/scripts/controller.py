import requests
import json

def getCalcInfo(name, url, results):
  res= json.loads(requests.get(url).text)
  results[name] = res

