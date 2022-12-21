import random
import json

def getRandPoints(num: int):
  randnum_dict = {}
  q = int(num/2) + 1
  pos_dict = {}
  sum_num = 0
  for i in range(num):
    randnum_dict[i] = random.randrange(2, q) # 個数
    sum_num += randnum_dict[i]
    tmp = {}
    check = []
    for j in range(randnum_dict[i]):
      flag = True
      rand_y = 0
      while flag:
        rand_y = random.randrange(num)
        if not rand_y in check:
          flag = False
      pos = [i, rand_y] # 座標
      check.append(rand_y)
      tmp[j] = pos
    pos_dict[i] = tmp
  # print(randnum_dict)
  # print(pos_dict)
  # print(sum_num)
  return pos_dict

def getRandEdge(grid_num):
  # 0 -> East, 1 -> South, 2 -> West, 3 -> North
  dire = ["e", "s", "w", "n"]
  d_num = random.randrange(4)
  d = dire[d_num] 
  edge = random.randrange(grid_num)
  return f"{d}{edge}"


def generate_routefile(grid_num: int, v_num: int, spec: int):
  pos_dict = getRandPoints(grid_num)
  s_dict = {}
  s_list = []
  with open("../sim_xml/random.rou.xml", "w") as routes:
    print("""<routes>
  <vType id="car" vClass="passenger" speedDev="0.2" sigma="0.2" decel="4.5" accel="2.6" maxSpeed="60" length="5"/>""", file=routes) # はじめ
    # レシーバー
    sid = 0
    for i in range(len(pos_dict)):
      for _, pos in pos_dict[i].items():
        x, y = "", ""
        if pos[0] < 10:
          x = f"0{pos[0]}"
        else:
          x = f"{pos[0]}"
        if pos[1] < 10:
          y = f"0{pos[1]}"
        else:
          y = f"{pos[1]}"
        edge = f"ns{x}{y}"
        print(f"""
  <vehicle id="mec{sid}" type="car" depart="0" color="1, 0, 0" departPos="stop">
    <route edges="{edge}"/>
    <stop edge="{edge}" lane="{edge}_0" parking="true"/>
    <param key="has.btreceiver.device" value="true"/> 
  </vehicle>""", file=routes)
        tmp = {}
        tmp["sid"] = f"mec{sid}"
        tmp["stype"] = "edge"
        tmp["spec"] = spec
        tmp["position"] = {"x": pos[0], "y": pos[1]}
        s_list.append(tmp)
        sid += 1
    s_dict["servers"] = s_list
    print(sid)

    # センダー
    vid = 0
    max_time = 100000
    for i in range(v_num):
      beg = getRandEdge(grid_num)
      end = beg
      while(beg == end):
        end = getRandEdge(grid_num)
      print(f"""
  <flow id=\"car{vid}\" type=\"car\" departPos=\"base\" number=\"1\" begin=\"0\" end=\"{max_time}\" from=\"{beg}\" to=\"-{end}\"/>
    <param key="has.btsender.device" value="true"/> 
  </flow>""", file=routes)
      vid += 1
    print("</routes>", file=routes) # おわり
    return s_dict

if __name__ == "__main__":
  # num = 10
  # pos_dict = getRandPoints(num)
  # for i in range(num):
  #   # print(chr(ord('A')+i))
  #   print(i)
  #   for j, pos in pos_dict[i].items():
  #     print(pos)
  
  spec = 10
  s_dict = generate_routefile(10, 300, spec) 
  with open('../sim_xml/servers.json', 'w') as f:
    json.dump(s_dict, f, ensure_ascii=False, indent=2)
