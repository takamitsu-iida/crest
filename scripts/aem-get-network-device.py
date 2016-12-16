#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMで管理しているデバイス一覧を入手します.

GET /network-device
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
  a = apicem.RestClient()

  api = '/network-device'
  r = a.get(api=api)

  if r.get('status_code', -1) < 0:
    print("サーバから情報を取得できませんでした")
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  device = data.get('response', [])
  if device == []:
    print("No network device found !")
    exit()

  device_list = []
  for item in device:
    device_list.append([item['hostname'], item['managementIpAddress'], item['type'], item['id']])

  print(tabulate(device_list, headers=['hostname', 'ip', 'type'], tablefmt='rst'))
