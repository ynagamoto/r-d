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
from tools import load_emission, load_servers_json, load_vehicles, setServersComm, showServersResource
from algo import loadAllocation, kizon, kizonLoad, envUpdate, exportNowLoad, exportResult, newExportNowLoad, exportStatus, exportVehiclesResult, allocateRandomServer, exportOverRate, loadOnly

def run(sumocfg):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  f = True
  res_num = 0
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    if f:
      res_num = int(traci.vehicle.getIDCount())
      f = False
    # print(f"now: {int(traci.simulation.getTime())}, v_num: {res_num - int(traci.vehicle.getIDCount())}")
    # print(f"now: {int(traci.simulation.getTime())}, v_num: {int(traci.vehicle.getIDCount())}")
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
"""

def randomAllocation(sumocfg, servers, servers_comm, vehicles, mig_time, res, gnum, ap, cloud):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  loads = []
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    allocateRandomServer(now, servers, vehicles, vid_list, servers_comm, mig_time, res, gnum, ap, cloud)
    # showServersResource(now, servers)

    load = newExportNowLoad(now, servers, servers_comm, res)
    load["cloud"] = cloud.idle_list[now]
    load["vehicles"] = len(vid_list) - len(servers)
    loads.append(load)

  # 結果の収集
  file_name = "random-runtime.csv"
  exportVehiclesResult(file_name, servers, vehicles, res, ap, gnum)
  file_name = "random-load.csv"
  exportResult(file_name, loads)
  file_name = "random-service.csv"
  exportStatus(file_name, servers, vehicles)
  file_name = "random-over.csv"
  exportOverRate(file_name, loads)
  traci.close()


"""
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
"""

def presend(sumocfg, servers, servers_comm, vehicles, mig_time, res, gnum, ap, cloud):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  loads= []
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    loadAllocation(now, servers, vehicles, vid_list, servers_comm, mig_time, res, gnum, ap, cloud)
    # showServersResource(now, servers)
    
    load = newExportNowLoad(now, servers, servers_comm, res)
    load["cloud"] = cloud.idle_list[now]
    load["vehicles"] = len(vid_list) - len(servers)
    loads.append(load)

  # 結果の収集
  file_name = "teian-runtime.csv"
  exportVehiclesResult(file_name, servers, vehicles, res, ap, gnum)
  file_name = "teian-load.csv"
  exportResult(file_name, loads)
  file_name = "teian-service.csv"
  exportStatus(file_name, servers, vehicles)
  file_name = "teian-over.csv"
  exportOverRate(file_name, loads)
  traci.close()


def kizonPresend(sumocfg, servers, servers_comm, vehicles, mig_time, res, gnum, ap, cloud):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  loads = []
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    kizon(now, servers, vehicles, vid_list, servers_comm, mig_time, res, gnum, ap, cloud)

    load = newExportNowLoad(now, servers, servers_comm, res)
    load["cloud"] = cloud.idle_list[now]
    load["vehicles"] = len(vid_list) - len(servers)
    loads.append(load)

  # 結果の収集
  file_name = "kizon-runtime.csv"
  exportVehiclesResult(file_name, servers, vehicles, res, ap, gnum)
  file_name = "kizon-load.csv"
  exportResult(file_name, loads)
  file_name = "kizon-service.csv"
  exportStatus(file_name, servers, vehicles)
  file_name = "kizon-over.csv"
  exportOverRate(file_name, loads)
  traci.close()

def kizonFix(sumocfg, servers, servers_comm, vehicles, mig_time, res, gnum, ap, cloud):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  loads = []
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    kizonLoad(now, servers, vehicles, vid_list, servers_comm, mig_time, res, gnum, ap, cloud)
    load = newExportNowLoad(now, servers, servers_comm, res)
    load["cloud"] = cloud.idle_list[now]
    load["vehicles"] = len(vid_list) - len(servers)
    loads.append(load)

  # 結果の収集
  file_name = "kizon-fix-runtime.csv"
  exportVehiclesResult(file_name, servers, vehicles, res, ap, gnum)
  file_name = "kizon-fix-load.csv"
  exportResult(file_name, loads)
  file_name = "kizon-fix-servce.csv"
  exportStatus(file_name, servers, vehicles)
  file_name = "kizon-fix-over.csv"
  exportOverRate(file_name, loads)
  traci.close()

def loadOnlyPresend(sumocfg, servers, servers_comm, vehicles, mig_time, res, gnum, ap, cloud):
  sumoBinary = "sumo"
  # sumoBinary = "sumo-gui"
  traci.start([sumoBinary, "-c", sumocfg])

  now = 0
  loads= []
  while traci.simulation.getMinExpectedNumber() > 0:
    # シミュレーション内容
    traci.simulationStep()
    
    now = int(traci.simulation.getTime())
    vid_list = traci.vehicle.getIDList()
    print(f"now: {now}, vehicles: {len(vid_list)-len(servers)}")

    envUpdate(traci, now, servers, vid_list, vehicles)
    loadOnly(now, servers, vehicles, vid_list, servers_comm, mig_time, res, gnum, ap, cloud)
    # showServersResource(now, servers)
    
    load = newExportNowLoad(now, servers, servers_comm, res)
    load["cloud"] = cloud.idle_list[now]
    load["vehicles"] = len(vid_list) - len(servers)
    loads.append(load)

  # 結果の収集
  file_name = "loadonly-runtime.csv"
  exportVehiclesResult(file_name, servers, vehicles, res, ap, gnum)
  file_name = "loadonly-load.csv"
  exportResult(file_name, loads)
  file_name = "loadonly-service.csv"
  exportStatus(file_name, servers, vehicles)
  file_name = "loadonly-over.csv"
  exportOverRate(file_name, loads)
  traci.close()


if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  gnum = 10
  mig_time = 10
  res = 2
  ap = 0.01
  vnum = 1500
  run(sumocfg)
  sim_time, emission = load_emission()
  sim_time += 2
  servers = load_servers_json(sim_time)
  # cloud
  cloud = Server("cloud", "cloud", [0, 0], 200, sim_time)
  vehicles = load_vehicles(sim_time, emission, vnum)
  print(f"sim time: {sim_time}, emission: {len(emission)}, vehicles: {len(vehicles)}")
  # presend(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res, gnum, ap, cloud)
  # kizonPresend(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res, gnum, ap, cloud)
  # kizonFix(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res, gnum, ap, cloud)
  # randomAllocation(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res, gnum, ap, cloud)
  # loadOnlyPresend(sumocfg, servers, setServersComm(sim_time, servers, vehicles), vehicles, mig_time, res, gnum, ap, cloud)


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