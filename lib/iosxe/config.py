#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""設定情報"""

#
# IOS-XEデバイス情報
#
xe_devices = {
  '10.35.185.11': {
    'protocol': "https",
    'port': 55443,  # IOS-XEのデフォルトのポート番号は55443
    'username': "cisco",
    'password': "cisco"
  }
}

#
# プロキシ設定
#
use_proxy = False
# use_proxy = True

proxies = {
  'http': "http://username:password@servername:8080",
  'https': "http://username:password@servername:8080"
}

if not use_proxy:
  proxies = None
