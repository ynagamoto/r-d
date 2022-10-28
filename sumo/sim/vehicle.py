"""
Vehicle Class
"""
from typing import Dict, List 

class Vehicle:
  # def __init__(self, vid: str, positions: Dict[int, List[float, float]], comm: Dict[str, List[float, float]]):
  def __init__(self, vid: str, positions: Dict[int, List[float]], comm: Dict[str, List[float]], sim_time: int):
    self.vid:               str = vid
    self.positions:         Dict[int, List[float]] = positions
    self.setCommServer(comm, sim_time)                          # comm: List[str]
    self.comm_server:       str = ""                            # server id
    self.comm_server_type:  str = ""
    self.exec_server:       str = ""                            # server id
    self.exec_server_type:  str = ""
    # self.change_flag:       bool = False
    self.mig_timer:         int  = 0
  
  def setCommServer(self, comm: Dict[str, List[float]], sim_time: int):
    self.comm = ["base"] * sim_time            # 0 ~ sim_time まで RSUなら "通信先id"，モバイル回線なら "base"
    for res_id, comm_time in comm.items():     # comm_time: [0: beg, 1: end]
      for i in range(int(comm_time[0]+1), int(comm_time[1]+1)):
        comm[i] = res_id
  
  def getCommServer(self, now: int) -> str:
    return self.comm[now]
  
  def getMigFlag(self) -> bool:
    if self.mig_timer == 0:
      return False
    else:
      return True
  
  def subMigTimer(self):
    self.mig_timer -= 1
  
  def isChangeComm(self, now) -> bool:
    if now == 0:
      return True
    else:
      if self.getCommServer(now-1) != self.getCommServer(now):
        return True
      else:
        return False
  
  def nextChangeTime(self, now: int) -> int:   # 次にいつ通信先が変わるか
    next_time = -1
    now_dest = self.comm[now]
    for i in range(now+1, len(self.comm)):
      if now_dest != self.comm[i]:
        next_time = i
        break
    return next_time

  def getDelay(self) -> float:
    res = 0
    if self.comm_server == self.exec_server: 
      res = 0
    else:
      if self.comm_server_type == "base":
        res += 20
      if self.exec_server_type == "rsu":
        res += 10
      else:
        res = res + 30
    return float(res)

