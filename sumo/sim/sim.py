from __future__ import absolute_import
from __future__ import print_function

import os
import sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci

from server import Server, Task
from vehicle import Vehicle
from tools import load_emission, load_servers_json, load_vehicles, setServersComm
from algo import getRandomServer, loadAllocation, envUpdate, exportNowLoad, exportResult, kizon

def run(sumocfg):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
  traci.close()

"""
def sim(sumocfg):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    vid_list = traci.vehicle.getIDList()
    for vid in vid_list:
      traci.vehicle.getPosition(vid)
  traci.close()
  sys.stdout.flush()
"""

def random_allocation(sumocfg, servers, vehicles, mig_time):
  sumoBinary = "sumo"
  traci.start([sumoBinary, "-c", sumocfg])
  res_num = 1

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(now)

    # マイグレーション状況の更新
    for vid in vid_list:
      v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
      if len(v_list) == 0: # receiver は vehicles に入ってない
        continue
      v = v_list[0]
      v.subMigTimer()

      # 通信サーバの更新
      now_s = v.getCommServer(now)
      if now_s == v.next_s:
        v.next_prep = False

    # ランダム再配置
    for vid in vid_list:
      v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
      if len(v_list) == 0: # receiver は vehicles に入ってない
        continue
      v = v_list[0]
      print(v.vid)

      # マイグレーション中，マイグレーションが完了している場合はスキップ
      if v.getMigFlag():
        continue 

      # 次のRSUと何秒通信開始するか調べる
      next_s, beg, end = v.getNextComm(now)
      rem = (beg-now) - mig_time # 猶予
      # 各車両がどこと通信しているか
      # now_s = v.getCommServer(now)

      if rem <= 0: # 猶予0で再配置
        while True:
          # ランダムなサーバのIDを取得
          new_s = getRandomServer(now, servers)
          print(new_s.sid)

          # 選んだサーバが mig_time 後以降 ~ 通信先が変わるまで空いているか調べる
          if new_s.resCheck(res_num, beg, end):
            # 空いていたら確保してループを抜ける
            new_s.resReserv(vid, res_num, beg, end)
            break

        # 確保できたら車両の状態を変更
        # if now_s.sid != new_s.sid:
        #   v.setMigTimer(mig_time)
        v.setMigTimer(mig_time)
        v.setNextCommServer(next_s)
    print()

  traci.close()
  sys.stdout.flush()


def test(sumocfg, servers, vehicles):
  sumoBinary = "sumo"
  traci.start([sumoBinary, "-c", sumocfg])

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(now)

    # マイグレーション状況の更新
    for vid in vid_list:
      v = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
      if len(v) == 1: # receiver は vehicles に入ってない
        print(v[0].vid)
    print()
 

def presend(sumocfg, servers, servers_comm, vehicles, mig_time, res):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  result = {}
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    loadAllocation(now, servers, vehicles, vid_list, servers_comm, mig_time, res)
    
    result[now] = exportNowLoad(now, servers)

  # 結果の収集
  file_name = "result.csv"
  exportResult(file_name, result)
  traci.close()

def kizonPresend(sumocfg, servers, servers_comm, vehicles, mig_time, res):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  result = {}
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    kizon(now, servers, vehicles, vid_list, servers_comm, mig_time, res)
    result[now] = exportNowLoad(now, servers)

  # 結果の収集
  file_name = "kizon.csv"
  exportResult(file_name, result)
  traci.close()

if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  mig_time = 10
  res = 2
  run(sumocfg)
  sim_time, emission = load_emission()
  sim_time += 2
  servers = load_servers_json(sim_time)
  vehicles = load_vehicles(sim_time, emission)
  print(f"sim time: {sim_time}")
  presend(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res)
  # kizonPresend(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res)
  # random_allocation(sumocfg, servers, vehicles, mig_time)
  # test(sumocfg, servers, vehicles)

"""
if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  mig_time = 10
  res = 1
  run(sumocfg)
  sim_time, emission = load_emission()
  sim_time += 1
  servers = load_servers_json(sim_time)
  vehicles = load_vehicles(sim_time, emission)
  print(f"sim time: {sim_time}")
"""