#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMで管理しているホスト一覧を取得します。

GET /host
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
except ImportError as e:
  logging.error("tabulateモジュールのインポートに失敗しました")
  logging.error(e)
  exit()

try:
  from apicem import apicem
except ImportError as e:
  logging.error("apicemモジュールのインポートに失敗しました")
  logging.error(e)
  exit()

###############################################################################

if __name__ == '__main__':

  # RestClientクラスをインスタンス化
  a = apicem.RestClient()

  # /hostにアクセスしてホスト一覧を得る
  api = '/host'
  r = a.get(api=api)

  # 戻り値をチェック
  # ステータスコードが負の場合は、何かおかしかったということ
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  # jsonの中身を確認
  # import json
  # print(json.dumps(r, indent=2))

  # apic-emからのデータは'data'キーに格納されている
  data = r.get('data', {})

  host_list = []
  for item in data.get('response', []):
    host_list.append([item['hostIp'], item['hostType'], item['connectedNetworkDeviceIpAddress']])

  print(tabulate(host_list, headers=['host IP', 'type', 'connected to network device'], tablefmt='rst'))
