import random
import json

def getRandPoints(num: int):
  gene_num = num + 1
  randnum_dict = {}
  q = int(num/2)
  limit = int(num*4/5)
  pos_dict = {}
  sum_num = 0
  for i in range(gene_num):
    randnum_dict[i] = random.randrange(q, limit) # 個数
    sum_num += randnum_dict[i]
    tmp = {}
    check = []
    for j in range(randnum_dict[i]):
      flag = True
      rand_y = 0
      while flag:
        rand_y = random.randrange(1, gene_num) # 1 ~ num まで
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

def getRandBeg(grid_num):
  d_num = random.randrange(4) # 方角
  edge = random.randrange(1, grid_num+2) # 1 ~
  
  if d_num == 0: # West
    return f"A{edge}B{edge}"
  elif d_num == 1: # South
    d = chr(ord('A')+edge)
    return f"{d}{0}{d}{1}"
  elif d_num == 2: # East
    d = chr(ord('A')+grid_num+2)
    bef_d = chr(ord('A')+grid_num+2-1)
    return f"{d}{edge}{bef_d}{edge}"
  elif d_num == 3: # North
    d = chr(ord('A')+edge)
    return f"{d}{grid_num+2}{d}{grid_num+1}"

def getRandEnd(grid_num):
  d_num = random.randrange(4) # 方角
  edge = random.randrange(1, grid_num+2) # 1 ~
  
  if d_num == 0:
    return f"B{edge}A{edge}"
  elif d_num == 1:
    d = chr(ord('A')+edge)
    return f"{d}{1}{d}{0}"
  elif d_num == 2:
    d = chr(ord('A')+grid_num)
    bef_d = chr(ord('A')+grid_num-1)
    return f"{bef_d}{edge}{d}{edge}"
  elif d_num == 3:
    d = chr(ord('A')+edge)
    return f"{d}{grid_num+1}{d}{grid_num+2}"

def generate_routefile(grid_num: int, v_num: int, spec: int):
  pos_dict = getRandPoints(grid_num)
  # チェック用
  for i in range(num+1):
    # print(chr(ord('A')+i))
    print(i)
    for _, pos in pos_dict[i].items():
      print(pos)
  print()

  s_dict = {}
  s_list = []
  with open("../sim_xml/random.rou.xml", "w") as routes:
    print("""<routes>
  <vType id="car" vClass="passenger" speedDev="0.2" sigma="0.2" decel="4.5" accel="2.6" maxSpeed="60" length="5"/>
  """, file=routes) # はじめ
    # レシーバー
    sid = 0
    for i in range(len(pos_dict)):
      for _, pos in pos_dict[i].items():
        x_pos = pos[0]+1
        y_pos = pos[1]+1
        alp = chr(ord('A')+x_pos)
        if pos[1] == num:
          edge = f"{alp}{y_pos-1}{alp}{y_pos}"
        else:
          edge = f"{alp}{y_pos}{alp}{y_pos+1}"
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
    print(sid) # レシーバーが合計で何台か

    # センダー
    vid = 0
    max_time = 100000
    for i in range(v_num):
      beg = getRandBeg(grid_num)
      end = beg
      while(beg == end):
        end = getRandEnd(grid_num)
      print(f"""
  <flow id=\"car{vid}\" type=\"car\" departPos=\"base\" number=\"1\" begin=\"0\" end=\"{max_time}\" from=\"{beg}\" to=\"{end}\">
    <param key="has.btsender.device" value="true"/> 
  </flow>""", file=routes)
      vid += 1
    print("</routes>", file=routes) # おわり
    return s_dict

if __name__ == "__main__":
  num = 10
  # num = 4
  spec = 20 # 10台
  # spec = 4
  s_dict = generate_routefile(num, 1000, spec) 
  with open('../sim_xml/servers.json', 'w') as f:
    json.dump(s_dict, f, ensure_ascii=False, indent=2)
