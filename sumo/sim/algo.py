import random
from typing import List, Dict
from server import Server, Task


# TODO
# 再配置計算をする必要があるか
# 次のRSUといつからいつまで通信するか (beg, end)
# 再配置＆車両の状態変化


# RSUの計算資源を t = beg ~ t = end まで確保できるかどうかチェック
def checkServerResource(beg: int, end:int, server: Server) -> bool:
  tmp_dict = server.idle_list[beg:end+1]
  res = List(filter(lambda item: item == 0, tmp_dict))
  if len(res) == 0:
    return True
  else:
    return False

# ランダム選択
def getRandomServer(now: int, servers: List[Server]) -> Server:
  sid = random.randrange(len(servers))
  return servers[sid]