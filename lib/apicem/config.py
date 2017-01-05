#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""設定情報"""

#
# APIC-EM
#
hostname = "devnetapi.cisco.com/sandbox/apic_em"
username = "devnetuser"
password = "Cisco123!"
version = "v1"

#
# プロキシ設定
#
use_proxy = False
# use_proxy = True

proxies = {
  'http': "http://username:password@proxyserver:8080",
  'https': "http://username:password@proxyserver:8080"
}

if not use_proxy:
  proxies = None
