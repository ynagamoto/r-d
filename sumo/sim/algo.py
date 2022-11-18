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

# TODO
# 提案手法
"""
1. 環境の更新
  1-1. マイグレーション状況の更新
  1-2. 各車両の通信先の更新
2. 次のRSUと何秒から何秒まで通信するか取得（beg, end）
3. 再配置計算が必要かチェック
  3-1. 次のRSUと通信するまでの時間 == マイグレーションにかかる時間
4. リソース予約状況の収集
5. 車両と各計算資源の通信遅延を収集
6. 再配置計算
  6-1.  計算資源の負荷にマイグレーション負荷を足して計算する
7. リソース確保 
"""