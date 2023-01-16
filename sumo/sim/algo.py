import random
from typing import List, Dict
from server import Server, Task
from vehicle import Vehicle, Comm
from tools import setServersComm, getTrafficJams, getServersLoads, getNowCommNum

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
def loadAllocation(now: int, servers: List[Server], vehicles: List[Vehicle], vid_list: List[str], servers_comm: Dict[int ,List[str]], mig_time: int, res: int, gnum: int, ap: float, cloud: Server):
  # 混雑度取得
  jams = getTrafficJams(now, servers_comm, servers) # 混雑度大きい順
  revers_jams = list(reversed(jams)) # 混雑度が小さい順
  # 混雑度から再配置の優先順位を取得
  mig_priority, need_list = checkMigNeed(now, mig_time, vid_list, vehicles, jams)
  # mig_priority, need_list = checkMigNeed(now, mig_time, vid_list, vehicles, revers_jams)
  print(f"\n---now: {now}, comm_num: {getNowCommNum(now, servers_comm)}")
  for sid in mig_priority:      # 優先度が高い順から再配置計算
    print(f"sid: {sid}")
    for tmp in need_list[sid]:  # tmp[0] -> Comm, tmp[1] -> Vehicle
      comm = tmp[0]
      v = tmp[1]
      print(f"  vid: {v.vid}, beg: {comm.time[0]}, end: {comm.time[1]}")
      beg, end = int(comm.time[0]), int(comm.time[1])
      next_sid, flag = v.getNextSid(now)
      if not flag: # マップから消える
        continue
      tmp_list = list(filter(lambda s: s.sid == next_sid, servers))
      next_s = tmp_list[0]
      # 再配置先の計算
      # beg ~ end で再配置可能な計算資源のリソース予約状況と通信遅延を取得
      loads = getServersLoads(now, comm.time, res, servers)

      # 配置できる計算資源がない
      if len(loads) == 0:
        # cloud に配置
        mig_fin = now+mig_time-1
        s_delay = next_s.getDelay2Calc(cloud, gnum)
        cloud.resReserv(v.vid, res/2, s_delay, now, mig_fin, "mig")
        cloud.resReserv(v.vid, res, s_delay, mig_fin+1, end, "ready")
        v.setCalcServer(cloud.sid, beg, end)
        print("----- Resource Error: Not enough capacity. now: {now}, vid: {v.vid}. -----")

      # 遅延を足してソート
      inds = {}
      for sid, load in loads.items():
        s_list = list(filter(lambda s: s.sid == sid, servers))
        calc = s_list[0]
        delay = next_s.getDelay2Calc(calc, gnum)
        inds[sid] = (ap/load) + delay # TODO chekc

      # 合計が最小のものを調べる
      sorted_inds = sorted(inds.items(), key = lambda ind: ind[1])
      locate_sid = sorted_inds[0][0]
      """
      locate_sid = ""
      for sid, _ in sorted_inds:
        locate_sid = sid
        break
      """

      # sid からサーバーを取得
      tmp_list= list(filter(lambda server: server.sid == locate_sid, servers))
      locate_server = tmp_list[0]
      s_delay = next_s.getDelay2Calc(locate_server, gnum)

      # リソース予約
      # VM起動中は半分の負荷
      mig_fin = now+mig_time-1
      locate_server.resReserv(v.vid, res/2, s_delay, now, mig_fin, "mig")
      locate_server.resReserv(v.vid, res, s_delay, mig_fin+1, end, "ready")
      v.setCalcServer(locate_sid, beg, end)


# 環境の更新
def envUpdate(traci, now: int, servers: List[Server], vid_list: List[str], vehicles: List[Vehicle]):
  # サーバのタスクとマイグレーション状況を更新 
  """
  for server in servers:
    server.updateResource(now)
  """

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
      if not (now >= v.comm_list[0].time[0] and now <= v.comm_list[0].time[1]): # 一番最初の通信はしょうがないので無視
        # サービスが受けられない場合はエラー
        comm, f = v.getNowComm(now)
        print(f"----- Error: {v.vid} could not receive the service.(now: {now}, sid: {calc_server.sid}, beg: {comm.time[0]}, end: {comm.time[1]}, lane: {traci.vehicle.getLaneID(v.vid)}) -----")
        for task in calc_server.tasks[now]:
          print(f"  vid: {task.vid}, type: {task.ttype}")
      else:
        print("--- 初期配置 ---")


# 再配置計算が必要かチェック 
# 再配置が必要な comm のリストを返す
# 混雑度順 -> List[str], Dict[str, List[]]
def checkMigNeed(now: int, mig_time: int, vid_list: List[str], vehicles: List[Vehicle], jams: Dict[str, List[str]]):
  # 混雑度順から need_list を作成
  # jams は通信先が多い順
  mig_priority = [] # 優先度高い順のsid
  need_list = {}    # key -> sid, value -> List[Vehicle]
  for tmp in jams: # sort すると dict じゃないことに注意
    mig_priority.append(tmp[0]) # sidを追加
    need_list[tmp[0]] = []
  # いま必要かどうかチェックする
  for vid in vid_list:
    # receiver は無視
    v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
    if len(v_list) == 0: # receiver は vehicles に入ってない
      continue
    v = v_list[0]
    
    f = False
    tmp_time = now
    while True:
      # この通信時間中のタスクの再配置計算を行ったかチェック
      # 計算済みなら次へ通信を調べる
      comm, flag = v.getNextComm(tmp_time)
      if not flag: # 次の通信先がない（マップから消える）
        break
      # print(f"\nnow = {now}")
      # print(f"  vid: {v.vid}, beg: {comm.time[0]}, end: {comm.time[1]}")
      if comm.flag:
        tmp_time = comm.time[1]+1
        # print("  -> skip")
      else:
        # そのRSUと通信するまでの猶予 ＝＝ マイグレーションにかかる時間のとき再配置計算を行う
        # print(f"now: {now}, vid: {v.vid}, beg: {comm.time[0]}, end: {comm.time[1]}")
        if int(comm.time[0])-now <= mig_time: # |t-1|tの再配置|t|t+1の再配置|t+1| なので，残りmig_timeでいい
          # 再配置計算が必要
          comm.flag = True
          # print("  do!")
          sid = comm.sid
          need_list[sid].append([comm, v])
          tmp_time = comm.time[1]+1
        else:
          # print("  break")
          break
  # 必要な comm をリターン
  """
  print(f"---check: {now}")
  for sid, hoge in need_list.items():
    for tmp in hoge:
      comm = tmp[0]
      v = tmp[1]
      print(f"  vid: {v.vid}, beg: {comm.time[0]}, end: {comm.time[1]}")
  print()
  """
  return mig_priority, need_list

def kizon(now: int, servers: List[Server], vehicles: List[Vehicle], vid_list: List[str], servers_comm: Dict[int ,List[str]], mig_time: int, res: int, gnum: int, ap: float, cloud):
  # 混雑度取得
  jams = getTrafficJams(now, servers_comm, servers)
  # 混雑度から再配置の優先順位を取得 
  mig_priority, need_list = kizonCheckMigNeed(now, mig_time, vid_list, vehicles, jams)
  # 再配置計算前の付加状況を取得
  s_idles = {}
  f = True
  s_spec = 0
  for s in servers:
    if f:
      s_spec = s.spec
      f = False
    s_idles[s.sid] = s.idle_list[now]
  # 再配置計算
  for sid in mig_priority:      # 優先度が高い順から再配置計算
    for tmp in need_list[sid]:  # tmp[0] -> Comm, tmp[1] -> Vehicle
      comm = tmp[0]
      v = tmp[1]
      beg, end = int(comm.time[0]), int(comm.time[1])
      next_sid, flag = v.getNextSid(now)
      if not flag: # マップから消える
        continue
      # sid からインスタンスを取得
      tmp_list = list(filter(lambda s: s.sid == next_sid, servers))
      next_s = tmp_list[0]
      # 再配置先の計算
      # 現在の負荷を集める
      loads = {}
      for s, idle in s_idles.items():
        # これ以上配置できないものは追加しない
        if idle-res >= 0:
          loads[sid] = idle/s_spec
      
      # 配置できる計算資源がない
      if len(loads) == 0:
        # cloud に配置
        mig_fin = now+mig_time-1
        s_delay = next_s.getDelay2Calc(cloud, gnum)
        cloud.resReserv(v.vid, res/2, s_delay, now, mig_fin, "mig")
        cloud.resReserv(v.vid, res, s_delay, mig_fin+1, end, "ready")
        v.setCalcServer(cloud.sid, beg, end)
        print("----- Resource Error: Not enough capacity. now: {now}, vid: {v.vid}. -----")

      # 遅延を足してソート
      inds = {}
      for sid, load in loads.items():
        s_list = list(filter(lambda s: s.sid == sid, servers))
        calc = s_list[0]
        delay = next_s.getDelay2Calc(calc, gnum)
        inds[sid] = (ap/load) + delay

      sorted_inds = sorted(inds.items(), key = lambda ind: ind[1])
      # 合計が最小のものを調べる
      locate_sid = ""
      for sid, _ in sorted_inds:
        locate_sid = sid
        break

      # sid からインスタンスを取得
      tmp_list= list(filter(lambda server: server.sid == locate_sid, servers))
      locate_server = tmp_list[0]
      s_delay = next_s.getDelay2Calc(locate_server, gnum)

      # リソース予約
      # VM起動中は半分の負荷
      mig_fin = now+mig_time-1
      locate_server.resReserv(v.vid, res/2, s_delay, now, mig_fin, "mig")
      locate_server.resReserv(v.vid, res, s_delay, mig_fin+1, end, "ready")
      comm.flag = True
      s_idles[locate_sid] -= res
      v.setCalcServer(locate_sid, beg, end)

def kizonCheckMigNeed(now: int, mig_time: int, vid_list: List[str], vehicles: List[Vehicle], jams: Dict[str, List[str]]):
  # 混雑度順から need_list を作成
  # jams は通信先が多い順
  mig_priority = [] # 優先度高い順のsid
  need_list = {}    # key -> sid, value -> List[Vehicle]
  for tmp in jams: # sort すると dict じゃないことに注意
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
    # 今通信が切断したかどうか
    if v.checkCommDownNow(now):
      # 切断したので再配置計算が必要
      next_sid = next_comm.sid
      need_list[next_sid].append([next_comm, v])
  return mig_priority, need_list

def exportNowLoad(now: int, servers: List[Server], res: int, ap: float):
  max_fps = 200
  result = {}
  result["now"] = now
  over = 0
  for s in servers:
    result[f"{s.sid}-idle"] = s.idle_list[now]
    idle = 0
    if s.idle_list[now] < 0:
      idle = res
      over = s.load_list[now]-s.spec
    else:
      idle = s.idle_list[now]+res
    param = idle/(s.spec+over)
    for task in s.tasks[now]:
      if task.ttype == "ready":
        result[f"{s.sid}-{task.vid}"] = (ap/param) + task.delay
    result[f"{s.sid}-fps"] = max_fps / (idle/s.spec)
  return result
  
def exportResult(file_name: str, result):
  # csvに出力
  df = pandas.json_normalize(result)
  df.to_csv(file_name, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)

def exportStatus(file_name: str, servers: List[Server], vehicles: List[Vehicle]):
  results = []
  for v in vehicles:
    result = {}
    result["vid"] = v.vid
    for comm in v.comm_list:
      beg = int(comm.time[0])
      calc_sid = v.calc_list[beg]
      tmp = list(filter(lambda s: s.sid == calc_sid, servers))
      calc_s = tmp[0]
      if not calc_s.checkTask(beg, v.vid):
        # サービスが受けられない場合は何秒遅れるか記録
        t = beg+1
        while True:
          if calc_s.checkTask(t, v.vid):
            break
        result[calc_s.sid] = t - beg
      results.append(result)

  df = pandas.json_normalize(results)
  df.to_csv(file_name, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
