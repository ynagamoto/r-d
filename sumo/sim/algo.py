import random
from typing import List, Dict
from server import Server, Task
from vehicle import Vehicle, Comm


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
  1-2. サービスを受けられるかチェック -> server.checkTask() 
  1-3. 車両の通信状況の更新 <- 通信先のリストを使う管理に変える
2. 混雑度を算出
3. 再配置計算が必要かチェックし再配置が必要な通信時間のリストを返す -> checkMigNeed()
  3-1. 車両が now 以降にどのRSUと何秒から何秒まで通信するかのリスト取得 ( {sid, [beg, end]} のリスト) v.getCommServers()
  3-2. それぞれの通信時間をfor文で回す
    3-2-1. その通信時間のタスクがマイグレーション中かチェック
    3-2-2. そのRSUと通信するまでの猶予 ＝＝ マイグレーションにかかる時間のとき再配置計算を行う
4. リソース予約状況の収集 -> s.getTimeOfLoads()
5. 車両と各計算資源の通信遅延を収集 -> s.getTimeOfLoads() TODO
6. 再配置計算 -> loadAllocation()
  6-1.  計算資源の負荷にマイグレーション負荷を足して計算する
7. リソース確保&リソース予約状況の更新 -> s.addTask()
8. 結果の収集 -> TODO
  8-1. フレームレートの計算 TODO
"""
def loadAllocation(now: int, servers: List[Server], vehicles: Dict[str, Vehicle], vid_list: List[str], mig_time: int):
  # 再配置計算を行う車両 vid_list
  for vid in vid_list:
    # receiver は無視
    v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
    if len(v_list) == 0: # receiver は vehicles に入ってない
      continue
    v = v_list[0]

    # 再配置計算が必要かチェック
    migtime_list = checkMigNeed(now, mig_time, v)
    for mig in migtime_list:
      pass

# 環境の更新
def envUpdate(now: int, servers: List[Server], vid_list: List[str], vehicles: Dict[str, Vehicle]):
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

    # サービスが受けられるかチェック手 乾燥
    comm_sid = v.getCommServer(now) # 現在通信しているサーバーのid
    s_list = list(filter(lambda server: server.sid == comm_sid, servers)) # idからサーバを取得
    comm_server = s_list[0]
    if not comm_server.checkTask(v.vid):
      # サービスが受けられない場合はエラー
      print(f"----- Error: {v.vid} could not receive the service. -----")


# 再配置計算が必要かチェック 
# 再配置が必要な comm のリストを返す
def checkMigNeed(now: int, mig_time: int, vehicle: Vehicle) -> List[Comm]:
  # 車両が now 以降にどのRSUと何秒から何秒まで通信するかのリスト取得 ( {sid: str, flag: bool, time: [beg, end]} のリスト)
  # それぞれの通信時間をfor文で回す
  need_list = []
  for comm in vehicle.getCommServers(now):
    # この通信時間中のタスクの再配置計算を行ったかチェック
    # 計算済みなら次へ
    if comm.flag:
      continue
    
    # そのRSUと通信するまでの猶予 ＝＝ マイグレーションにかかる時間のとき再配置計算を行う
    if comm.time[0]-now <= mig_time:
      # 再配置計算が必要
      need_list.append(comm)
    else:
      # comm は時系列順なのでここで再配置が必要なければこれ以降も必要ない
      break
    
  # 必要な comm をリターン
  return need_list