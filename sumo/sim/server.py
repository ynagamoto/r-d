"""
Server Class
"""
from typing import Dict, List
from copy import copy

class Task:
  def __init__(self, vid: str, resource: int, delay: float, ttype: str):
    self.vid        : str = vid                                     # Vehicle ID
    self.resource   : int = resource                                # Required resource
    self.delay      : float = delay                                 # Delay from vehicle to server 
    self.ttype      : str = ttype

  def show(self):
    print(f"vid: {self.vid}, res: {self.resource}, timer: {self.timer}")

class Server:
  def __init__(self, sid: str, stype: str, postion: Dict[str, int], spec: int, sim_time: int):
    self.sid        : str = sid                                     # Server ID
    self.stype      : str = stype                                   # Server type (edge, middle or cloud)
    self.postion    : Dict[str, int] = postion                      # Server postion: {x: float, y: float}
    self.spec       : int = spec                                    # Server's computing resource
    self.idle_list  : List[int] = [spec] * sim_time                 # Idling resource: {time: int, idel: float}
    self.tasks      : Dict[int, List[Task]] = {}                    # tasks: {time: int, [ {vid: str, resource: int, delay: float} ]}
    self.initTasks(sim_time)
    self.sim_time   : int = sim_time
    self.comm       : Dict[int, List[str]] = {}
  
  def initTasks(self, sim_time:int):
    for i in range(sim_time):
      self.tasks[i] = []

  def addTask(self, task: Task, time: int):
    self.tasks[time].append(task)
    self.idle_list[time] -= task.resource
  
  # 使わない
  """
  def removeTask(self, vid: str) -> bool:
    blen = len(self.tasks)
    print(self.tasks)
    self.tasks = list(filter(lambda task : task.vid != vid, self.tasks))
    print(self.tasks)
    if blen == len(self.tasks):
      return False
    return True
  """
  
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
  
  # beg ~ end の負荷
  def getTimeOfLoads(self, beg: int, end:int): # [float, List[Task]]:
    sum_idle = 0
    for i in range(beg, end+1):
      sum_idle += self.idle_list[i]
    ave_idle = sum_idle/(end-beg+1) # 平均idle
    return ave_idle/self.spec
  
  def resCheck(self, res:int, beg: int, end: int) -> bool: # 指定した時間帯のリソースが空いているか調べる
    for i in range(beg, end+1):
      if self.idle_list[i]-res < 0:
        return False
    return True 
  
  def resReserv(self, vid:str, res:int, delay, beg: int, end: int, ttype): # 指定した時間帯のリソースを確保
    # task.show()
    for i in range(beg, end+1):
      task = Task(vid, res, delay, ttype)
      self.addTask(task, i)

  # 使わない
  # マイグレーション状況を更新する
  """
  def updateResource(self, now: int):
    load = 0
    for i in range(now, len(self.tasks)):
      for task in self.tasks[i]:
        if not task.status == "ready":
          task.timer -= 1
          if task.timer == 0:
            task.status = "ready"
        # print(f"now: {now}, sid: {self.sid}, vid: {task.vid}, timer: {task.timer}, status: {task.status}")
        if task.status == "mig":
          load += task.resource/2
        elif task.status == "ready":
          load += task.resource
        else:
          print("!!!!!!!!!!")
    if now < len(self.idle_list):
      print(f"sid: {self.sid}, idle: {self.idle_list[now]}")
  """

  # TODO
  # 変更に合わせる  
  # vid のタスクが now_task に含まれていて提供可能かどうかチェック
  def checkTask(self, now: int, vid: str) -> bool:
    task = list(filter(lambda task: task.vid == vid, self.tasks[now]))
    if len(task) > 0:
      if task[0].ttype== "ready":
        return True
      else:
        return False
    else:
      print("!!!!!")
      return False
 
  # Calculate delay from vehicle to server
  # gnum = 10 のとき
  # g0 -> 0 <= x <= 5,  0 <= y <= 5
  # g1 -> 6 <= x <= 10, 0 <= y <= 5
  # g2 -> 0 <= x <= 5,  6 <= y <= 10
  # g3 -> 6 <= x <= 10, 6 <= y <= 10
  def getPosGroup(self, gnum) -> str:
    g = ""
    half = int(gnum/2)
    if self.postion["y"] <= half:
      if self.postion["x"] <= half:
        g = "g0"
      else:
        g = "g1"
    else:
      if self.postion["x"] <= half:
        g = "g2"
      else:
        g = "g3"
    return g
    
  # calc までの遅延
  def getDelay2Calc(self, calc: str, gnum: int):
    """
    そのRSUで処理   -> 0
    同じグループ    -> 10
    別のグループ    -> 20
    クラウドで処理  -> 40
    """
    if calc.stype == "cloud":
      return 40
    my_pg = self.getPosGroup(gnum)
    calc_pg = calc.getPosGroup(gnum)
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
