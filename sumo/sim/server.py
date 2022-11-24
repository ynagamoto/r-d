"""
Server Class
"""
from typing import Dict, List
from copy import copy

class Task:
  def __init__(self, vid: str, resource: int, delay: float, timer: int):
    self.vid        : str = vid                                     # Vehicle ID
    self.resource   : int = resource                                # Required resource
    self.delay      : float = delay                                 # Delay from vehicle to server 
    self.timer      : int = timer

class Server:
  def __init__(self, sid: str, stype: str, postion: Dict[str, int], spec: int, sim_time: int):
    self.sid        : str = sid                                     # Server ID
    self.stype      : str = stype                                   # Server type (edge, middle or cloud)
    self.postion    : Dict[str, int] = postion                      # Server postion: {x: float, y: float}
    self.spec       : int = spec                                    # Server's computing resource
    self.idle_list  : List[int] = [spec] * sim_time                 # Idling resource: {time: int, idel: int}
    self.tasks      : Dict[int, List[Task]] = {}                    # tasks: {time: int, [ {vid: str, resource: int, delay: float} ]}
    self.initTasks(sim_time)
    self.sim_time   : int = sim_time
  
  def initTasks(self, sim_time:int):
    for i in range(sim_time):
      self.tasks[i] = []

  # !!!!!!!!!!   WILL   !!!!!!!!!!
  # 挙動があやしい
  def addTask(self, task: Task, time: int):
    self.tasks[time].append(task)
    self.idle_list[time] -= task.resource
  
  # 使わない
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
  
  def getResAve(self, beg: int, end:int) -> bool:
    res_sum = 0
    for i in range (beg, end+1):
      res_sum += self.idle_list[i]
    return res_sum/(end-beg+1)
  
  # !!!!!!!!!!   WILL   !!!!!!!!!!
  # beg ~ end の負荷
  def getTimeOfLoads(self, beg: int, end:int) -> [float, List[Task]]:
    res_list = []
    sum_load = 0
    for i in range(beg, end+1):
      res_list.append(self.tasks[i])
      for task in self.tasks[i]:
        sum_load += task.resource
    return sum_load/(end-beg+1), res_list
  
  # !!!!!!!!!!   WILL   !!!!!!!!!!
  # resCheck と resReserv を一つのメソッドにする
  def resCheck(self, res:int, beg: int, end: int) -> bool: # 指定した時間帯のリソースが空いているか調べる
    for i in range(beg, end+1):
      if self.idle_list[i]-res < 0:
        return False
    return True 
  
  def resReserv(self, vid:str, res:int, beg: int, end: int, timer: int): # 指定した時間帯のリソースを確保
    task = Task(vid, res, 0, timer)
    for i in range(beg, end+1):
      self.addTask(task, i)

  # マイグレーション状況を更新する
  def updateResource(self, now: int):
    for i in range(now, self.sim_time):
      for task in self.tasks[i]:
        if task.timer > 0:
          task.timer -= 1

  # vid のタスクが now_task に含まれていて提供可能かどうかチェック
  def checkTask(self, vid: str, now: int) -> bool:
    task_list = self.tasks[now] 
    res = list(filter(lambda task: task.vid == vid, task_list))
    if len(res) > 0:
      if res[0].timer == 0:
        return True
      else:
        return False
    else:
      return False
 
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
  server = Server("s0", "edge", {"x": 0.0, "y": "0.0"}, 100, 100)
  server.addTask(Task("v0", 10, 10, 3), 0); server.addTask(Task("v1", 10, 10, 3), 0); server.showTaskList()

  task = server.getTask("v0"); print(f"vid: {task.vid}, resource: {task.resource}, delay: {task.delay}\n"); server.showTaskList()
  
  print(server.removeTask("v0")); server.showTaskList()

if __name__ == "__main__":
  test()
