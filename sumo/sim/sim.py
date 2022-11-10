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
from tools import generate_routefile, load_emission, load_servers, load_vehicles 
from algo import getRandomServer

def run(sumocfg):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
  traci.close()

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

def random_allocation(sumocfg, servers, vehicles):
  sumoBinary = "sumo"
  traci.start([sumoBinary, "-c", sumocfg])
  mig_time = 3
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
      if v.getMigFlag():
        v.subMigTimer()

    # 通信先が切り替わったタイミングでランダムな計算資源に割り振る
    for vid in vid_list:
      v_list = list(filter(lambda vehicle: vehicle.vid == vid, vehicles))
      if len(v_list) == 0: # receiver は vehicles に入ってない
        continue
      v = v_list[0]
      print(v.vid)
  
      # 次のRSUと何秒通信開始するか調べる
      _, beg, end = v.getNextComm(now)
      rem = (beg-now) - mig_time # 猶予
      # 各車両がどこと通信しているか
      # now_s = v.getCommServer(now)

      if rem <= 0: # 猶予0で再配置
        while True:
          # ランダムなサーバのIDを取得
          new_s = getRandomServer(now, servers)

          # 選んだサーバが mig_time 後以降 ~ 通信先が変わるまで空いているか調べる
          if new_s.resCheck(res_num, beg, end) :
            # 空いていたら確保してループを抜ける
            new_s.resReserv(vid, res_num, beg, end)
            break

        # 確保できたら車両の状態を変更
        # if now_s.sid != new_s.sid:
        #   v.setMigTimer(mig_time)
        v.setMigTimer(mig_time)
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
 

if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  # generate_routefile()
  run(sumocfg)
  sim_time, emission = load_emission()
  servers = load_servers(sim_time)
  vehicles = load_vehicles(sim_time, emission)
  random_allocation(sumocfg, servers, vehicles)
  # test(sumocfg, servers, vehicles)
