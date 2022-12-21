"""
Vehicle Class
"""
from typing import Dict, List 

class Vehicle:
  # def __init__(self, vid: str, positions: Dict[int, List[float, float]], comm: Dict[str, List[float, float]]):
  def __init__(self, vid: str, positions: Dict[int, List[float]], comm: Dict[str, List[float]], sim_time: int):
    self.vid                : str = vid
    self.positions          : Dict[int, List[float]] = positions
    self.setCommServer(comm, sim_time)                          # self.comm: List[str]
    self.comm_list          : List[Comm] = []
    self.setCommList(comm)
    self.now_comm           : Comm = None
    self.comm_org           : Dict[str, List[float]] = comm     # comm: [sid, [beg, end]]
    # self.comm_server        : str = ""                            # server id
    # self.comm_server_type   : str = ""
    # self.exec_server        : str = ""                            # server id
    # self.exec_server_type   : str = ""
    # self.mig_timer          : int  = 0
    # self.next_prep:         bool = False
    # self.next_s:            str = "" 
  
  def setCommServer(self, comm: Dict[str, List[float]], sim_time: int):
    self.comm = ["base"] * (sim_time+1)     # 0 ~ sim_time まで RSUなら "通信先id"，モバイル回線なら "base"
    for sid, comm_time in comm.items():     # comm_time: [0: beg, 1: end]
      for i in range(int(comm_time[0]+1), int(comm_time[1]+1)):
        self.comm[i] = sid
  
  def getCommServer(self, now: int) -> str:
    return self.comm[now]

  # 車両がどのRSUと何秒から何秒まで通信するかのリストを作成 ( {sid, [beg, end]} のリスト)
  def setCommList(self, comm):
    for sid, comm_time in comm.items():     # comm_time: [0: beg, 1: end]
      self.comm_list.append(Comm(sid, comm_time))
        
  # 車両が now 以降にどのRSUと何秒から何秒まで通信するかのリスト取得 ( {sid, [beg, end]} のリスト)
  # getNextComm を改良する
  def getCommServers(self, now):
    # beg が now 以降の comm を追加
    res_comm = list(filter(lambda comm: comm.time[0] >= now, self.comm_list))
    return res_comm

  # 再配置計算済みに更新
  def updateCommFlag(self, sid: str):
    tmp = list(filter(lambda comm: comm.sid == sid, self.comm_list))
    tmp[0].flag = True


  # migTimer は使用しない
  # server でマイグレーション状況を管理する
  # vehicle は再配置計算を行ったかどうかだけ
  """
  def setMigTimer(self, mig_time: int):
    self.mig_timer = mig_time

  def getMigFlag(self) -> bool:
    if self.next_prep:
      return True
    else:
      if self.mig_timer == 0:
        return False
      else:
        return True
  
  def subMigTimer(self):
    if self.getMigFlag():
      self.mig_timer -= 1
      if self.mig_timer == 0:
        self.next_prep = True

  def setNextCommServer(self, next_s: str):
    self.next_s = next_s
  
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
  """
  
  # 次のRSUのIDを取得
  def getNextSid(self, now: int):
    comm_list = list(filter(lambda comm: comm.time[0] >= now, self.comm_list))
    next_comm = comm_list[0]
    return next_comm.sid

  # 遅延を取得
  # 改良が必要 TODO
  """
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
  """

"""
各車両が通信状況を管理するためのクラス
"""
class Comm:
  def __init__(self, sid: str, comm: List[float]):
    self.sid    : str                 # 通信するサーバid
    self.time   : List[float] = comm  # 通信時間 [beg, end]
    self.flag   : bool = False        # 再配置計算を行ったかどうか
