"""
Server Class
"""
from typing import Dict, List
from copy import copy

class Task:
  def __init__(self, vid: str, resource: int, delay: float, timer: int):
    self.vid        : str = vid                                     # Vehicle ID
    self.resource   : int = resource                                # Required resource
    # self.delay      : float = delay                                 # Delay from vehicle to server 
    self.timer      : int = timer
    if timer < 0:
      self.status = ""
    else:
      self.status     : str = "mig"                                   # mig のときは必要リソースの半分
  def show(self):
    print(f"vid: {self.vid}, res: {self.resource}, timer: {self.timer}")

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
    self.comm       : Dict[int, List[str]] = {}
  
  def initTasks(self, sim_time:int):
    for i in range(sim_time):
      self.tasks[i] = []

  # !!!!!!!!!!   !WILL   !!!!!!!!!!
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
  
  # !!!!!!!!!!   !WILL   !!!!!!!!!!
  # beg ~ end の負荷
  def getTimeOfLoads(self, beg: int, end:int): # [float, List[Task]]:
    res_list = []
    sum_load = 0
    for i in range(beg, end+1):
      res_list.append(self.tasks[i])
      for task in self.tasks[i]:
        if task.status == "mig":
          sum_load += task.resource/2
        else:
          sum_load += task.resource
    return sum_load/(end-beg+1), res_list
  
  def resCheck(self, res:int, beg: int, end: int) -> bool: # 指定した時間帯のリソースが空いているか調べる
    for i in range(beg, end+1):
      if self.idle_list[i]-res < 0:
        return False
    return True 
  
  def resReserv(self, vid:str, res:int, beg: int, end: int, mig_time: int): # 指定した時間帯のリソースを確保
    task = Task(vid, res, 0, mig_time)
    # task.show()
    for i in range(beg, end+1):
      self.addTask(task, i)

  # マイグレーション状況を更新する
  def updateResource(self, now: int):
    load = 0
    for i in range(now, len(self.tasks)):
      for task in self.tasks[i]:
        if task.timer > 0:
          task.timer -= 1
          if task.timer == 0:
            task.status = "ready"
        if task.status == "mig":
          load += task.resource/2
        elif task.status == "ready":
          load += task.resource
        else:
          print("!!!!!!!!!!")
    if now < len(self.idle_list):
      print(f"sid: {self.sid}, idle: {self.idle_list[now]}")

  # vid のタスクが now_task に含まれていて提供可能かどうかチェック
  def checkTask(self, now: int, vid: str) -> bool:
    task_list = self.tasks[now] 
    task = list(filter(lambda task: task.vid == vid, task_list))
    if len(task) > 0:
      if task[0].status == "ready":
        return True
      else:
        return False
    else:
      print("!!!!!")
      return False
 
  # Calculate delay from vehicle to server
  # g0 -> 0 <= x <= 4, 0 <= y <= 4
  # g1 -> 5 <= x <= 9, 0 <= y <= 4
  # g2 -> 0 <= x <= 4, 5 <= y <= 9
  # g3 -> 5 <= x <= 9, 5 <= y <= 9
  def getPosGroup(self) -> str:
    g = ""
    if self.postion["y"] < 5:
      if self.postion["x"] < 5:
        g = "g0"
      else:
        g = "g1"
    else:
      if self.postion["x"] < 5:
        g = "g2"
      else:
        g = "g3"
    return g
    
  def getDelay2Calc(self, calc: str):
    """
    そのRSUで処理   -> 0
    同じグループ    -> 10
    別のグループ    -> 20
    クラウドで処理  -> 40
    """
    if calc.stype == "cloud":
      return 40
    my_pg = self.getPosGroup()
    calc_pg = calc.getPosGroup()
    delay = 0
    if self.sid == calc.sid:
      delay = 0
    elif my_pg == calc_pg:
      delay = 10
    else:
      delay = 20
    return delay

  # スペック，負荷状況，タスク，遅延を返す
  def getNowLoad(self, now: int):
    return self.spec, self.idle_list[now], self.tasks[now]


def test():
  server = Server("s0", "edge", {"x": 0.0, "y": "0.0"}, 100, 100)
  server.addTask(Task("v0", 10, 10, 3), 0); server.addTask(Task("v1", 10, 10, 3), 0); server.showTaskList()

  task = server.getTask("v0"); print(f"vid: {task.vid}, resource: {task.resource}, delay: {task.delay}\n"); server.showTaskList()
  
  print(server.removeTask("v0")); server.showTaskList()

if __name__ == "__main__":
  test()
