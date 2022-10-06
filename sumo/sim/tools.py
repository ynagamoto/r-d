import json
from server import Server,Task
from typing import List
import random
import xml.etree.ElementTree as ET

def load_server():
  file_name = "server.json"
  with open(file_name) as f:
    mec_list = json.load(f)
  
  servers = []
  tmp_task = Task("v0", 10, 10)
  for mec in mec_list["servers"]:
    server = Server(mec["sid"], mec["stype"], mec["position"], mec["spec"])
    servers.append(server)
  return servers

def print_servers(servers: List[Server]):
  for server in servers:
    print(f"sid: {server.sid}, stype: {server.stype}, spec: {server.spec}")

def get_random_edge(gridnum, edgenum):
  edgetype = random.randint(0, 100) % 2
  rand1 = random.randint(0, 100) % edgenum 
  rand2 = random.randint(0, 100) % (gridnum - 1)
  tempedge = chr(65+rand1) + f"{rand2}"
  if edgetype == 1:
    tempedge = f"-{tempedge}"
  return tempedge
  
def generate_routefile():
  vnum = 100 # number of vehicles
  gridnum = 4
  edgenum = gridnum*2
  with open("random.rou.xml", "w") as routes:
    print("""<routes>
    <vType id="car" vClass="passenger" speedDev="0.2" sigma="0.2" decel="4.5" accel="2.6" maxSpeed="60" length="5"/>

    """, file=routes) # はじめ
    for i in range(vnum):
      beg = get_random_edge(gridnum, edgenum)
      end = beg
      while(beg == end):
        end = get_random_edge(gridnum, edgenum)
      print(f"<flow id=\"car{i}\" type=\"car\" departPos=\"base\" number=\"1\" begin=\"0\" end=\"300\" from=\"{beg}\" to=\"{end}\"/>", file=routes)
    print("</routes>", file=routes) # おわり

def load_emission():
  file_name = "emission.xml"
  tree = ET.parse(file_name)
  root = tree.getroot()

  vehicles = {}
  # init json
  vnum = 100
  for i in range(vnum):
    car_id = f"car{float(i)}"
    vehicles[car_id] = {
      "x": [],
      "y": [],
      "pos": []
    }
  
  # sort each vehicle in time
  for timestep in root:
    now = int(float(timestep.attrib["time"]))
    for vehicle in timestep:
      # tmp = vehicle.attrib["id"].rsplit("car")
      # car_id = int(float(tmp[1]))
      car_id = vehicle.attrib["id"]
      pos = [float(vehicle.attrib["x"]), float(vehicle.attrib["y"])]
      vehicles[car_id]["x"].append(pos[0])
      vehicles[car_id]["y"].append(pos[1])
      vehicles[car_id]["pos"].append(pos)
      vehicles[car_id][now] = pos
  return vehicles

def load_bt():
  file_name = "bt.xml"
  tree = ET.parse(file_name)
  root = tree.getroot()

  vnum = 100
  vehicles = {}
  for i in range(vnum):
    car_id = f"car{float(i)}"
    vehicles[car_id] = {
      "time": {}
    }
  
  # sort each vehicle in time at receiver 
  for receiver in root:
    for seen in receiver:
      car_id = seen.attrib["id"]
      comm_time = {
        "beg" :seen.attrib["tBeg"], 
        "end": seen.attrib["tEnd"]
      }
      vehicles[car_id]["time"][receiver.attrib["id"]] = comm_time
  return vehicles

if __name__ == "__main__":
  print_servers(load_server())