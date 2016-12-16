#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMで管理しているネットワークデバイスのIPアドレスを入手します.

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

  # RestClientクラスをインスタンス化
  a = apicem.RestClient()

  # /hostにアクセスしてホスト一覧を得る
  api = '/host'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  ip_list = []
  idx = 0
  for i, item in enumerate(data.get('response', [])):
    ip_list.append([i + 1, 'host', item['hostIp']])
    idx = i + 1

  # /network-deviceにアクセスしてネットワークデバイス一覧を得る
  api = '/network-device'
  r = a.get(api=api)
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  data = r.get('data', {})

  for i, item in enumerate(data.get('response', [])):
    ip_list.append([i + idx + 1, 'network device', item['managementIpAddress']])

  print(tabulate(ip_list, headers=['number', 'type', 'ip'], tablefmt='rst'))
