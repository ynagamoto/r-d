"""
Server Class
"""
from typing import Dict, List
from copy import copy

class Task:
  def __init__(self, vid: str, resource: int, delay: float):
    self.vid: str = vid                     # Vehicle ID
    self.resource: int = resource           # Required resource
    self.delay:float = delay                # Delay from vehicle to server 

class Server:
  def __init__(self, sid: str, stype: str, postion: Dict[str, int], spec: int):
    self.sid: str = sid                     # Server ID
    self.stype:str = stype                  # Server type (edge, middle or cloud)
    self.postion: Dict[str, int] = postion  # Server postion: {x: float, y: float}
    self.spec: int = spec                   # Server's computing resource
    self.idel: int = spec                   # Idling resource
    self.tasks: List[Task] = []             # tasks: [ {vid: str, resource: int, delay: float} ]
  
  def addTask(self, task: Task):
    self.tasks.append(task)
    self.idel -= task.resource
  
  def removeTask(self, vid: str) -> bool:
    blen = len(self.tasks)
    print(self.tasks)
    self.tasks = list(filter(lambda task : task.vid != vid, self.tasks))
    print(self.tasks)
    if blen == len(self.tasks):
      return False
    return True
  
  def getTask(self, vid: str):
    res = list(filter(lambda task : task.vid == vid, self.tasks))
    return res[0] 
  
  def getTaskList(self):
    return self.tasks
  
  def showTaskList(self):
    print("Show Task List")
    for task in self.tasks:
      print(f"vid: {task.vid}, resource: {task.resource}, delay: {task.delay}")
    print()

  # Calculate delay from vehicle to server
  def calcDelay(self, sid: str, vid: str):
    """
    車両がRSUの通信範囲内
      そのRSUで処理 -> 0
      別のRSU処理   -> 10 + 10 = 20 
      集約局で処理  -> 10
      クラウドで処理 -> 10 + 30 = 40
    車両がRSUの通信範囲外
      RSUで処理     -> 20 + 10 = 30
      集約局で処理  -> 20
      クラウドで処理 -> 20 + 40 = 60
    """
    delay = 0
    return delay

def test():
  server = Server("s0", "edge", {"x": 0.0, "y": "0.0"}, 100)
  server.addTask(Task("v0", 10, 10)); server.addTask(Task("v1", 10, 10)); server.showTaskList()

  task = server.getTask("v0"); print(f"vid: {task.vid}, resource: {task.resource}, delay: {task.delay}\n"); server.showTaskList()
  
  print(server.removeTask("v0")); server.showTaskList()

if __name__ == "__main__":
  test()
