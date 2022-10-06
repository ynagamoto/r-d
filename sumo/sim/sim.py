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
from tools import generate_routefile, load_server, load_emission, load_bt


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

if __name__ == "__main__":
  sumocfg = "sim.sumocfg"
  generate_routefile()
  run(sumocfg)
  sim(sumocfg)
