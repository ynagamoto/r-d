import random

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


def generate_routefile(grid_num: int, v_num: int):
  pos_dict = getRandPoints(grid_num)
  sid = 0
  with open("random.rou.xml", "w") as routes:
    print("""<routes>
    <vType id="car" vClass="passenger" speedDev="0.2" sigma="0.2" decel="4.5" accel="2.6" maxSpeed="60" length="5"/>""", file=routes) # はじめ
    # レシーバー
    for i in range(len(pos_dict)):
      for _, pos in pos_dict[i].items():
        edge = f"ns{pos[0]}{pos[1]}"
        print(f"""
        <vehicle id="rec{sid}" type="car" depart="0" color="1, 0, 0" departPos="stop">
          <route edges="{edge}"/>
          <stop edge="{edge}" lane="{edge}_0" parking="true"/>
          <param key="has.btreceiver.device" value="true"/> 
        </vehicle>""", file=routes)
        sid += 1

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

if __name__ == "__main__":
  # num = 10
  # pos_dict = getRandPoints(num)
  # for i in range(num):
  #   # print(chr(ord('A')+i))
  #   print(i)
  #   for j, pos in pos_dict[i].items():
  #     print(pos)
  generate_routefile(10, 100) 
