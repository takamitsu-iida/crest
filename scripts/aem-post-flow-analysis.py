#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMのパストレース

POST /flow-analysis
"""

import json
import logging
import os
import sys
import time  # sleep()

# 通常はWARN
# 多めに情報を見たい場合はINFO
logging.basicConfig(level=logging.INFO)

def here(path=''):
  """相対パスを絶対パスに変換して返却します"""
  return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

# libフォルダにおいたpythonスクリプトを読みこませるための処理
sys.path.append(here("../lib"))
sys.path.append(here("../lib/site-packages"))

try:
  from tabulate import tabulate
  from apicem import apicem
except ImportError as e:
  logging.error("モジュールのインポートに失敗しました")
  logging.error(e)
  exit()

###############################################################################

if __name__ == '__main__':

  a = apicem.RestClient()

  # デバイス一覧を作成
  idx = 0
  ip_list = []

  api = '/host'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  for i, item in enumerate(data.get('response', [])):
    ip_list.append([i+1, 'host', item['hostIp']])
    idx = i + 1

  api = '/network-device'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  for i, item in enumerate(data.get('response', [])):
    ip_list.append([i+idx+1, 'network device', item['managementIpAddress']])

  print(tabulate(ip_list, headers=['number', 'type', 'ip'], tablefmt='rst'))
  print("*** Please note that not all source/destination ip pair will return a path - no route. ! *** \n")

  # 送信元IPを選択
  s_ip = ""
  d_ip = ""
  ip_idx = 2
  while True:
    user_input = input('=> Select a number for the source IP from above list: ')
    user_input = user_input.strip()
    if user_input.lower() == 'exit':
      exit()
    if user_input.isdigit():
      if int(user_input) in range(1, len(ip_list)+1):
        s_ip = ip_list[int(user_input)-1][ip_idx]  # 2 is the position of IP
        break
      else:
        print("Oops! number is out of range, please try again or enter 'exit'")
    else:
      print("Oops! input is not a digit, please try again or enter 'exit'")
  # End of while loop
  print("*** Please note that not all source/destination ip pair will return a path - no route. ! *** \n")

  while True:
    user_input = input('=> Select a number for the destination IP from above list: ')
    user_input = user_input.strip()
    if user_input.lower() == 'exit':
      sys.exit()
    if user_input.isdigit():
      if int(user_input) in range(1, len(ip_list)+1):
        d_ip = ip_list[int(user_input)-1][ip_idx] # 2 is the position of IP
        break
      else:
        print("Oops! number is out of range, please try again or enter 'exit'")
    else:
      print("Oops! input is not a digit, please try again or enter 'exit'")
  # End of while loop

  # JSON input for POST /flow-analysis
  path_data = {
    'sourceIP': s_ip,
    'destIP': d_ip
  }
  api = '/flow-analysis'
  r = a.post(api=api, data=path_data)
  data = r.get('data', {})
  print("Response from POST /flow-analysis:\n", json.dumps(data, indent=2))

  response = data.get('response', {})
  taskId = response.get('taskId', None)
  if not taskId:
    logging.error("failed to get taskId")
    exit()

  api = '/task/' + taskId
  r = a.get(api=api)
  data = r.get('data', {})
  response = data.get('response', {})
  print("Response from GET /task/taskId:\n", json.dumps(data, indent=2))

  # When see the endTime field from response above means that get flow-path task is completed
  pathId = ""
  count = 0
  while pathId == "":
    count += 1
    if count > 30:
      print("No routing path was found. Please try using different source and destination !")
      exit(-1)

    endTime = response.get('endTime', None)
    if not endTime:
      # No endTime, no pathId yet
      print("\nTask is not finished yet, sleep 1 second then try again")
      time.sleep(1)
      r = a.get(api=api)
      data = r.get('data', {})
      response = data.get('response', {})
      print("Response from GET /task/taskId:\n", json.dumps(data, indent=2))
    else:
      # endTime exist,can get pathId now
      # pathId is the value of "progress" attribute
      if response["isError"] == 'true':
        print("\nSomething is wrong, here is the response:\n")
        print("\n*** Response from GET /flow-analysis/pathId.- Trace path information. ***\n", json.dumps(response, indent=2))
        print("\n------ End of path trace ! ------")
      else:
        pathId = response['progress']
        print("\nPOST flow-analysis task is finished now, here is the pathId: ", pathId)
        api = '/flow-analysis/' + pathId
        r = a.get(api=api)
        print("\n*** Response from GET /flow-analysis/pathId.- Trace path information. ***\n", json.dumps(r, indent=2))
        print("\n------ End of path trace ! ------")
