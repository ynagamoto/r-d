import json
from server import Server,Task
from vehicle import Vehicle
from typing import List,Dict
import random
import xml.etree.ElementTree as ET

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

def load_servers(sim_time: int):
  file_name = "server.json"
  with open(file_name) as f:
    mec_list = json.load(f)
  
  servers = []
  # tmp_task = Task("v0", 10, 10)
  for mec in mec_list["servers"]:
    server = Server(mec["sid"], mec["stype"], mec["position"], mec["spec"], sim_time)
    servers.append(server)
  return servers

def print_servers(servers: List[Server]):
  for server in servers:
    print(f"sid: {server.sid}, stype: {server.stype}, spec: {server.spec}")

def load_emission():
  file_name = "emission.xml"
  tree = ET.parse(file_name)
  root = tree.getroot()

  # sort each vehicle in time
  vehicles = {}
  sim_time = 0
  for timestep in root:
    now = int(float(timestep.attrib["time"]))
    sim_time = now
    for vehicle in timestep:
      car_id = vehicle.attrib["id"]
      if car_id not in vehicles:
        vehicles[car_id] = {}
      position = [float(vehicle.attrib["x"]), float(vehicle.attrib["y"])]
      vehicles[car_id][now] = position
  return sim_time, vehicles

def load_bt():
  file_name = "bt.xml"
  tree = ET.parse(file_name)
  root = tree.getroot()
 
  # sort each vehicle in time at receiver 
  vehicles = {}
  for receiver in root:
    for seen in receiver:
      car_id = seen.attrib["id"]
      if car_id not in vehicles:
        vehicles[car_id] = {}
      comm_time = [float(seen.attrib["tBeg"]), float(seen.attrib["tEnd"])]
      vehicles[car_id][receiver.attrib["id"]] = comm_time
  return vehicles

def load_vehicles(sim_time: int, emission: Dict[str, int]):
  bt = load_bt()
  # Apply to Vehicle Class
  vehicles = []
  for vid, postions in emission.items():
    comm = dict(filter(lambda bt: bt[0] == vid, bt.items()))
    if not any(comm): # comm is empty (this vid is receiver's id.)
      continue
    vehicle = Vehicle(vid, postions, comm[vid], sim_time)
    vehicles.append(vehicle)
  return vehicles

def print_vehicles(vehicles: List[Vehicle]):
  for vehicle in vehicles:
    print(vehicle.vid)
  print()
  for vehicle in vehicles:
    if (vehicle.vid == "car1.0"):
      print(vehicle.vid)
      print(vehicle.positions)
      print(vehicle.comm)
      break

if __name__ == "__main__":
  # print_servers(load_servers())
  # print_vehicles(load_vehicles())
  pass