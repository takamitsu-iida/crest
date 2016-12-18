#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""IOS-XEのテスト"""

import json
import logging
import os
import sys

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
  from iosxe import iosxe
except ImportError as e:
  logging.error("iosxeモジュールのインポートに失敗しました")
  logging.error(e)
  exit()

###############################################################################

if __name__ == '__main__':

  # RestClientクラスをインスタンス化
  xe = iosxe.RestClient(hostname="10.35.185.11")

  def show_running_config():
    """running configを表示"""
    RUNNING_CONFIG = "/api/v1/global/running-config"
    r = xe.get(RUNNING_CONFIG)
    data = r.get('data', None)
    print(data)

  def show_interfaces():
    """インタフェース状態を表示"""
    INTERFACES = "/api/v1/interfaces"
    r = xe.get(INTERFACES)
    data = r.get('data', None)
    print(json.dumps(data, indent=2))

  def show_route():
    """ルーティングテーブルを表示"""
    ROUTING_TABLE = "/api/v1/routing-svc/routing-table"
    r = xe.get(ROUTING_TABLE)
    data = r.get('data', None)
    print(json.dumps(data, indent=2))

  def show_cpu():
    """CPU使用率を表示"""
    CPU = "/api/v1/global/cpu"
    r = xe.get(CPU)
    data = r.get('data', None)
    print(json.dumps(data, indent=2))

  show_running_config()
  show_interfaces()
  show_route()
  show_cpu()
