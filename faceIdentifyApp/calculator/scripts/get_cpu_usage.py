import psutil

def getCpuUsage():
  cpu_usage = float(psutil.cpu_percent(interval=0.1))
  return cpu_usage
