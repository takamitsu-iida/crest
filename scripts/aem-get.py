#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMにGETして情報をダンプします。

使い方
aem-get.py URL
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
  from apicem import apicem
except ImportError as e:
  logging.error("apicemモジュールのインポートに失敗しました")
  logging.error(e)
  exit()

###############################################################################

def main(api=''):
  """メイン関数"""
  # RestClientクラスをインスタンス化
  a = apicem.RestClient()

  r = a.get(api=api)

  # 戻り値をチェック
  # ステータスコードが負の場合は、何かおかしかったということ
  if r.get('status_code', -1) < 0:
    logging.error("failed to GET %s", api)
    exit()

  # jsonの中身を確認
  import json
  print(json.dumps(r, indent=2))

if __name__ == '__main__':
  if len(sys.argv) == 1:
    print('Usage: # aem-get.py URL')
    exit()

  main(api=sys.argv[1])
