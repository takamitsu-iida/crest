#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMで管理しているデバイス一覧から装置を選んでインタフェース設定を入手します.

GET /network-device/ + id + /config
GET /interface/network-device/ + id
"""

import json
import logging
import os
import sys

# 通常はWARN
# 多めに情報を見たい場合はINFO
logging.basicConfig(level=logging.WARN)

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

  # RestClientクラスをインスタンス化
  a = apicem.RestClient()

  api = '/network-device'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  device = data.get('response', [])
  if device == []:
    print("No network device found !")
    exit()

  while True:
    user_input = input('=> Please enter \n1: To get list of interfaces for the given device ID\n2: To get IOS configuration for the given device ID\nEnter your selection: ')
    user_input = user_input.strip()
    if user_input.lower() == 'exit':
      exit()
    if user_input.isdigit():
      if user_input in {'1', '2'}:
        break
      else:
        print("please try again to select 1 or 2 or enter 'exit'!")
    else:
      print("please try again or enter 'exit'")
  #

  device_list = []
  device_show_list = []
  for i, item in enumerate(device):
    device_list.append([item["hostname"], item["managementIpAddress"], item["type"], item["instanceUuid"]])
    device_show_list.append([i+1, item["hostname"], item["managementIpAddress"], item["type"]])

  print(tabulate(device_show_list, headers=['number', 'hostname', 'ip', 'type'], tablefmt="rst"), '\n')

  did = ""
  device_id_idx = 3
  while True:
    if user_input == '1':
      print("*** Please note that some devices may not be able to show interface info for various reasons. ***\n")
      user_input2 = input('=> Select a number for the device from above to show Interface:')
    else:
      print("*** Please note that some devices may not be able to show configuration for various reasons. ***\n")
      user_input2 = input('=> Select a number for the device from above to show IOS config:')
    user_input2 = user_input2.strip()
    if user_input2.lower() == 'exit':
      exit()
    if user_input2.isdigit():
      if int(user_input2) in range(1, len(device_show_list)+1):
        did = device_list[int(user_input2)-1][device_id_idx]
        break
      else:
        print("please try again or enter 'exit'")
    else:
      print("please try again or enter 'exit'")
  #

  # show interface or IOS config
  if user_input == '1':
    # get interface list
    selected_api = "/interface/network-device/" + did
  else:
    # get IOS configuration
    selected_api = "/network-device/" + did + "/config"

  # GET
  r = a.get(api=selected_api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", selected_api)
    exit()

  data = r.get('data', {})

  if user_input == '1':
    # interface list
    print("Response:\n", json.dumps(data, indent=2))
  if user_input == '2':
    # IOS configuration
    print(data['response'])
