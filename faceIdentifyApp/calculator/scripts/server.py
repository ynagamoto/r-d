import socket

def info():
  return socket.gethostbyname(socket.gethostname())
