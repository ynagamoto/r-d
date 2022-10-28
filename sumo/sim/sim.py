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
from tools import generate_routefile, load_servers, load_vehicles 


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

  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()

    # マイグレーション状況の更新
    for vid in vid_list:
      if vehicles[vid].getMigFlag():
        vehicles[vid].subMigTimer()

    # 通信先が切り替わったタイミングでランダムな計算資源に割り振る
    for vid in vid_list:
      if vehicles[vid].isChangeComm(now):     # 通信先が切り替わった
        # 各車両がどこと通信しているか
        vehicles[vid].getCommServer(now)

        # 何ステップ後に次のRSUと通信開始するか調べる
        # 選んだサーバが mig_time 後以降 ~ 通信先が変わるまで空いているか調べる
        # 空いているならリソース確保，無理ならもう一度（3回選んでもだめならクラウドへ）
        # 確保できたら車両の状態を変更
  traci.close()
  sys.stdout.flush()



if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  generate_routefile()
  run(sumocfg)
  servers = load_servers()
  vehicles = load_vehicles()
  # sim(sumocfg)
