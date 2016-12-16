#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMで管理しているデバイス一覧から装置を選んでコンフィグを入手します.

GET /network-device/' + device_id + '/config
"""

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
    logging.error("no network device found")
    exit()

  device_list = []
  device_show_list = []
  for i, item in enumerate(device):
    device_list.append([item['hostname'], item['managementIpAddress'], item['type'], item['instanceUuid']])
    device_show_list.append([i+1, item['hostname'], item['managementIpAddress'], item['type']])

  print(tabulate(device_show_list, headers=['number', 'hostname', 'ip', 'type'], tablefmt='rst'), '\n')

  print("*** Please note that some devices may not be able to show configuration for various reasons. ***\n")

  # 標準入力からの入力待ち
  device_id = ""
  device_id_idx = 3
  while True:
    user_input = input('=> Select a number for the device from above to show IOS config:')
    user_input = user_input.strip()
    if user_input.lower() == 'exit':
      exit()
    if user_input.isdigit():
      if int(user_input) in range(1, len(device_show_list)+1):
        device_id = device_list[int(user_input)-1][device_id_idx]
        print(device_id)
        break
      else:
        print("please try again or enter 'exit'")
    else:
      print("please try again or enter 'exit'")
  #

  # コンフィグを入手する
  api = '/network-device/' + device_id + '/config'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})
  conf = data.get('response', "")
  print(conf)
