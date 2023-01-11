import random
from typing import List, Dict
from server import Server, Task
from vehicle import Vehicle, Comm
from tools import setServersComm, getTrafficJams, getServersLoads

import itertools
import pandas
import csv

# RSUの計算資源を t = beg ~ t = end まで確保できるかどうかチェック
def checkServerResource(beg: int, end:int, server: Server) -> bool:
  tmp_dict = server.idle_list[beg:end+1]
  res = List(filter(lambda item: item == 0, tmp_dict))
  if len(res) == 0:
    return True
  else:
    return False

# ランダム選択
def getRandomServer(now: int, servers: List[Server]) -> Server:
  sid = random.randrange(len(servers))
  return servers[sid]


# TODO
# 提案手法
"""
1. 環境の更新 -> envUpdate()
  1-1. サーバのタスクとマイグレーション状況を更新 -> server.updateResource()
    ※ VMの起動中は半分の負荷
  1-2. サービスを受けられるかチェック -> server.checkTask() 
  1-3. 車両の通信状況の更新 <- 通信先のリストを使う管理に変える
2. 混雑度を算出 -> getTrafficJams()
3. 再配置計算が必要かチェックし再配置が必要な通信時間のリストを返す -> checkMigNeed()
  3-1. 車両が now 以降にどのRSUと何秒から何秒まで通信するかのリスト取得 ( {sid, [beg, end]} のリスト) v.getCommServers()
  3-2. それぞれの通信時間をfor文で回す
    3-2-1. その通信時間のタスクがマイグレーション中かチェック
    3-2-2. そのRSUと通信するまでの猶予 == マイグレーションにかかる時間のとき再配置計算を行う
4. リソース予約状況の収集 -> s.getTimeOfLoads()
5. 車両と各計算資源の通信遅延を収集 -> s.getTimeOfLoads()
6. 再配置計算 -> loadAllocation()
  6-1.  計算資源の負荷にマイグレーション負荷を足して計算する
7. リソース確保&リソース予約状況の更新 -> s.addTask()
8. 結果の収集
  8-1. フレームレートの計算 TODO
"""
# servers_comm = setServersComm() 
def loadAllocation(now: int, servers: List[Server], vehicles: Dict[str, Vehicle], vid_list: List[str], servers_comm: Dict[int ,List[str]], mig_time: int, res: int):
  # 混雑度取得
  jams = getTrafficJams(now, servers_comm, servers)
  revers_jams = list(reversed(jams))
  # 混雑度から再配置の優先順位を取得
  # mig_priority, need_list = checkMigNeed(now, mig_time, vid_list, vehicles, jams)
  mig_priority, need_list = checkMigNeed(now, mig_time, vid_list, vehicles, revers_jams)
  for sid in mig_priority:      # 優先度が高い順から再配置計算
    for tmp in need_list[sid]:  # tmp[0] -> Comm, tmp[1] -> Vehicle
      comm = tmp[0]
      v = tmp[1]
      beg, end = int(comm.time[0]), int(comm.time[1])
      next_sid, flag = v.getNextSid(now)
      if not flag: # マップから消える
        continue
      tmp_list = list(filter(lambda s: s.sid == next_sid, servers))
      next_s = tmp_list[0]
      # 再配置先の計算
      # beg ~ end で再配置可能な計算資源のリソース予約状況と通信遅延を取得
      loads = getServersLoads(now, comm.time, res, servers)
      # 遅延を足してソート
      inds = {}
      for sid, load in loads.items():
        s_list = list(filter(lambda s: s.sid == sid, servers))
        calc = s_list[0]
        delay = next_s.getDelay2Calc(calc)
        inds[sid] = load + delay

      sorted_inds = sorted(inds.items(), key = lambda ind: ind[1])
      # 合計が最小のものを調べる
      locate_sid = ""
      for sid, _ in sorted_inds:
        locate_sid = sid
        break

      # sid からサーバーを取得
      tmp_list= list(filter(lambda server: server.sid == locate_sid, servers))
      locate_server = tmp_list[0]

      # リソース予約
      # VM起動中は半分の負荷
      locate_server.resReserv(v.vid, res, beg, end, mig_time)
      comm.flag = True
      v.setCalcServer(locate_sid, beg, end)


# 環境の更新
def envUpdate(traci, now: int, servers: List[Server], vid_list: List[str], vehicles: Dict[str, Vehicle]):
  # サーバのタスクとマイグレーション状況を更新 
  for server in servers:
    server.updateResource(now)

  # 現在地図上の車両は vid_list に vid が入っている
  for vid in vid_list: 
    # receiver は vehicles に入ってない
    v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
    if len(v_list) == 0: # receiver のときは入ってない
      continue
    v = v_list[0]

    # サービスが受けられるかチェック
    calc_sid = v.calc_list[now]                                             # 現在通信しているサーバーのid
    s_list = list(filter(lambda server: server.sid == calc_sid, servers))   # idからサーバを取得
    if len(s_list) == 0:
      continue
    calc_server = s_list[0]
    if not calc_server.checkTask(now, v.vid):
      if not (now >= v.comm_list[0].time[0] and now < v.comm_list[0].time[1]): # 一番最初の通信はしょうがないので無視
        # サービスが受けられない場合はエラー
        print(f"----- Error: {v.vid} could not receive the service.({traci.vehicle.getLaneID(v.vid)}) -----")


# 再配置計算が必要かチェック 
# 再配置が必要な comm のリストを返す
# 混雑度順 -> List[str], Dict[str, List[]]
def checkMigNeed(now: int, mig_time: int, vid_list: List[str], vehicles: List[Vehicle], jams: Dict[str, List[str]]):
  # 混雑度順から need_list を作成
  # jams は通信先が多い順
  mig_priority = [] # 優先度高い順のsid
  need_list = {}    # key -> sid, value -> List[Vehicle]
  for tmp in jams:
    mig_priority.append(tmp[0]) # sidを追加
    need_list[tmp[0]] = []

  # いま必要かどうかチェックする
  for vid in vid_list:
    # receiver は無視
    v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
    if len(v_list) == 0: # receiver は vehicles に入ってない
      continue
    v = v_list[0]
    
    # 次に通信する計算資源を取得
    comm, flag = v.getNextComm(now)
    if not flag: # 次の通信先がない（マップから消える）
      continue

    # この通信時間中のタスクの再配置計算を行ったかチェック
    # 計算済みなら次へ
    if comm.flag:
      continue
    
    # そのRSUと通信するまでの猶予 ＝＝ マイグレーションにかかる時間のとき再配置計算を行う
    if comm.time[0]-now <= mig_time+2:
      # 再配置計算が必要
      sid = comm.sid
      if not sid in need_list:
        need_list[sid] = []
      need_list[sid].append([comm, v])
    
  # 必要な comm をリターン
  return mig_priority, need_list

def exportNowLoad(now: int, servers: List[Server]):
  tmp = {}
  for s in servers:
    tmp[s.sid] = 0
    for task in s.tasks[now]:
      if task.status == "mig":
        tmp[s.sid] += task.resource/2
      else:
        tmp[s.sid] += task.resource
  return tmp
  
def exportResult(file_name: str, result):
  # csvに出力
  df = pandas.json_normalize(result)
  df.to_csv(file_name, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)

# servers_comm = setServersComm() 
def kizon(now: int, servers: List[Server], vehicles: Dict[str, Vehicle], vid_list: List[str], servers_comm: Dict[int ,List[str]], mig_time: int, res: int):
  # 混雑度取得
  jams = getTrafficJams(now, servers_comm, servers)
  # 混雑度から再配置の優先順位を取得 
  mig_priority, need_list = kizonCheckMigNeed(now, mig_time, vid_list, vehicles, jams)
  for sid in mig_priority:      # 優先度が高い順から再配置計算
    for tmp in need_list[sid]:  # tmp[0] -> Comm, tmp[1] -> Vehicle
      comm = tmp[0]
      v = tmp[1]
      beg, end = int(comm.time[0]), int(comm.time[1])
      next_sid, flag = v.getNextSid(now)
      if not flag: # マップから消える
        continue
      tmp_list = list(filter(lambda s: s.sid == next_sid, servers))
      next_s = tmp_list[0]
      # 再配置先の計算
      # 現在の負荷を集める
      loads = {}
      for s in servers:
        # これ以上配置できないものは追加しない
        if s.idle_list[now] > 0:
          loads[s.sid] = s.spec - s.idle_list[now]
      # 遅延を足してソート
      inds = {}
      for sid, load in loads.items():
        s_list = list(filter(lambda s: s.sid == sid, servers))
        calc = s_list[0]
        delay = next_s.getDelay2Calc(calc)
        inds[sid] = load + delay

      sorted_inds = sorted(inds.items(), key = lambda ind: ind[1])
      # 合計が最小のものを調べる
      locate_sid = ""
      for sid, _ in sorted_inds:
        locate_sid = sid
        break

      # sid からサーバーを取得
      tmp_list= list(filter(lambda server: server.sid == locate_sid, servers))
      locate_server = tmp_list[0]

      # リソース予約
      # VM起動中は半分の負荷
      locate_server.resReserv(v.vid, res, beg, end, -1)
      comm.flag = True
      v.setCalcServer(locate_sid, beg, end)

def kizonCheckMigNeed(now: int, mig_time: int, vid_list: List[str], vehicles: Dict[str, Vehicle], jams: Dict[str, List[str]]):
  # 混雑度順から need_list を作成
  # jams は通信先が多い順
  mig_priority = [] # 優先度高い順のsid
  need_list = {}    # key -> sid, value -> List[Vehicle]
  for tmp in jams:
    mig_priority.append(tmp[0]) # sidを追加
    need_list[tmp[0]] = []

  # いま必要かどうかチェックする
  for vid in vid_list:
    # receiver は無視
    v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
    if len(v_list) == 0: # receiver は vehicles に入ってない
      continue
    v = v_list[0]
    
    # 次に通信する計算資源を取得
    next_comm, flag = v.getNextComm(now)
    if not flag: # 次の通信先がない（マップから消える）
      continue
    if v.checkCommDown(now):
      # 再配置計算が必要
      next_sid = next_comm.sid
      if not next_sid in need_list:
        need_list[next_sid] = []
      need_list[next_sid].append([next_comm, v])
    
  return mig_priority, need_list