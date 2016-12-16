#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ノンブロッキングなパストレース処理."

POST /flow-analysis
"""

import json
import logging
import os
import sys
import time
import threading

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

a = apicem.RestClient()

def check_status(arg):
  """non-blocking wait function to check

  POST /flow-analysis status:
  INPROGRESS, COMPLETED, FAILED
  """

  status = arg
  count = 0
  while status != "COMPLETED":
    if status == "FAILED":
      print("Unable to find full path. No traceroute or netflow information found. Failing path calculation.")
      print("\n------ End of path trace ! ------")
      exit()
    print("\nTask is not finished yet, sleep 1 second then try again")
    time.sleep(1)
    count += 1
    if count > 30:
      print("\nNo routing path was found. Please try using different source and destination !")
      print("\n------ End of path trace ! ------")
      sys.exit()
    try:
      api = '/flow-analysis/' + flowAnalysisId
      resp = a.get(api=api)
      response_json = r.json()
      print("\nGET flow-analysis with flow-analysisId status: ", r.status_code)
      print("Response from GET /flow-analysis/"+flowAnalysisId, json.dumps(response_json, indent=2))
      status = response_json["response"]["request"]["status"]
    except:
      # Something is wrong
      print("\nSomething is wrong when executing get /flow-analysis/{flowAnalysisId}")
  print("\n------ End of path trace ! ------")

if __name__ == '__main__':

  ip_list = []
  flowAnalysisId = ''
  idx = 0
  ############################################
  # Create a list of host and network device #
  ############################################
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

  ####################
  # Select source ip #
  ####################
  s_ip = ""
  d_ip = ""
  ip_idx = 2
  while True:
    user_input = input('=> Select a number for the source IP from above list: ')
    user_input = user_input.replace(" ", "") # ignore space
    if user_input.lower() == 'exit':
      sys.exit()
    if user_input.isdigit():
      if int(user_input) in range(1, len(ip_list)+1):
        s_ip = ip_list[int(user_input)-1][ip_idx] # 2 is the position of IP
        break
      else:
        print("Oops! number is out of range, please try again or enter 'exit'")
    else:
      print("Oops! input is not a digit, please try again or enter 'exit'")
  # End of while loop

  #########################
  # Select destination ip #
  #########################
  while True:
    user_input = input('=> Select a number for the destination IP from above list: ')
    user_input = user_input.replace(" ", "") # ignore space
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

  ###############################
  # execute POST /flow-analysis #
  ###############################

  # JSON input for POST /flow-analysis
  path_data = {
    "sourceIP": s_ip,
    "destIP": d_ip
  }

  api = '/flow-analysis'
  r = a.post(api=api, data=path_data)
  response_json = r.json()
  print("\nPOST flow-analysis Status: ", r.status_code)
  print("Response from POST /flow-analysis:\n", json.dumps(response_json, indent=2))

  try:
    flowAnalysisId = response_json["response"]["flowAnalysisId"]
  except:
    print("\n For some reason cannot get flowAnalysisId")
    sys.exit()

  ####################################
  # Check status - non-blocking wait #
  ####################################
  thread = threading.Thread(target=check_status, args=('',))  # passing status = ''
  thread.start()

