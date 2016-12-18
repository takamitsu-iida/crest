#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
APIC-EMのREST APIへの接続機能を提供します。
依存外部モジュール
  requests
"""

import functools  # デコレータを作るのに必要
import json
import logging

logging.basicConfig(level=logging.INFO)

try:
  import requests
  # HTTPSを使用した場合に、証明書関連の警告を無視する
  requests.packages.urllib3.disable_warnings()
except ImportError:
  logging.error("requestsモジュールのインポートに失敗しました。")
  exit()

try:
  from .ticketmanager import ticketmanager
except ImportError:
  logging.error("ticketmanagerモジュールのインポートに失敗しました。")
  exit()


class RestClient(object):
  """APIC-EMのREST APIに接続する機能を提供します"""
  # pylint: disable=too-many-instance-attributes

  #
  # このクラスから戻す値のフォーマット
  # APIC-EMからのデータは★の部分に格納されている
  #
  # {
  #   "Content-Type": "application/json;charset=UTF-8",
  #   "status_code": 200,
  #   "data": {
  #     "version": "1.0",
  #     "response": ★
  #   }
  # }
  #

  def __init__(self):
    self._protocol = "https"
    self._port = 443
    self._timeout = 10
    try:
      # from . import _config as config  # _config is not tracked by git due to include password info
      from . import config  # need apic-em info in config.py
      self._hostname = config.hostname
      self._username = config.username
      self._password = config.password
      self._version = config.version
      self._proxies = config.proxies
    except ImportError:
      logging.info("configモジュールの読み込みに失敗しました。デフォルト設定を適用します。")
      self._hostname = "devnetapi.cisco.com/sandbox/apic_em"
      self._username = "devnetuser"
      self._password = "__________"
      self._version = "v1"
      self._proxies = None
    self._prefix = ""
    self.setPrefix()


  def setPrefix(self):
    """プレフィクスを作り直します"""
    if self._port == 443:
      self._prefix = "%s://%s" % (self._protocol, self._hostname)
    else:
      self._prefix = "%s://%s:%s" % (self._protocol, self._hostname, str(self._port))

  def getTicket(self):
    """スレッドセーフなチケット取得"""
    ticketmanager.lock()
    ticket = self._getTicket()
    ticketmanager.release()
    return ticket

  def _getTicket(self):
    """実際のチケット取得処理"""
    ticket = ticketmanager.ticket()
    if ticket:
      return ticket

    logging.info("trying to get new ticket from controller")

    # チケットを取得するための接続先
    url = self._prefix + "/api/" + self._version + "/ticket"

    # ヘッダ
    headers = {
      'Accept': "application/json, text/plain",
      'Content-Type': "application/json"
    }

    # 認証情報
    auth_json = {
      "username": self._username,
      "password": self._password
    }
    auth_data = json.dumps(auth_json)

    # タイムアウト値
    timeout = self._timeout

    # プロキシ
    proxies = self._proxies

    # POSTを発行
    try:
      r = requests.post(url, headers=headers, data=auth_data, timeout=timeout, proxies=proxies, verify=False)
      if r.status_code in [requests.codes.ok]:
        if r.headers['Content-Type'].find("json") >= 0:
          j = r.json()
          # response部分だけを取り出す
          ticket = j.get("response", None)
          # チケットマネージャに保管して
          ticketmanager.ticket(ticket)
          # あらためて取り出す
          ticket = ticketmanager.ticket()
          return ticket
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None
  #

  # 未使用・デコレータを使わない版
  # GET
  def _get(self, api="", params=""):
    """apiで指定したURLにHTTP GETで接続して、レスポンスをJSONで返します。"""
    # チケットを持っているか確認
    ticket = self.getTicket()
    if not ticket:
      logging.error("need a proper ticket to access rest api")
      return None

    headers = {
      'Accept': "application/json, text/plain",
      'Content-Type': "application/json",
      'X-Auth-Token': ticket['serviceTicket']
    }

    if not api.startswith('/'):
      api = '/' + api
    url = self._prefix + "/api/" + self._version + api
    timeout = self._timeout

    logging.info("GET '%s'", url)
    try:
      r = requests.get(url, timeout=timeout, headers=headers, params=params, verify=False, proxies=self._proxies)
      logging.info("status code : %s", r.status_code)
      if r.status_code in [requests.codes.ok]:
        # チケットは最後に使った時刻を記録して保存する
        ticketmanager.ticket(ticket)
        if r.headers['Content-Type'].find("json") >= 0:
          return r.json()
        return r.text
    except requests.exceptions.RequestException as e:
      logging.error(e)

    return None

  # デコレータ定義
  def set_ticket():
    """GET/POST/PUT/DELETEの前後処理をするデコレータ"""
    def _outer_wrapper(wrapped_function):
      @functools.wraps(wrapped_function)
      def _wrapper(self, *args, **kwargs):
        #
        # 前処理
        #

        # 戻り値は必ずオブジェクトを返す
        result = {}

        # チケットを取得
        ticket = self.getTicket()
        if not ticket:
          logging.error("failed to obtain ticket to access apic-em rest api")
          result['status_code'] = -10
          result['data'] = None
          return result

        # ヘッダにチケットを挿入
        headers = {
          'Accept': "application/json, text/plain",
          'Content-Type': "application/json",
          'X-Auth-Token': ticket['serviceTicket']
        }

        # タイムアウト値
        timeout = self.timeout()

        # プロキシ設定
        proxies = self.proxies()

        #
        # 実処理
        #
        r = wrapped_function(self, *args, headers=headers, timeout=timeout, proxies=proxies, verify=False, **kwargs)

        #
        # 後処理
        #

        if not r:
          logging.error("failed to access apic-em rest api")
          result['status_code'] = -1
          result['data'] = None
          return result

        if r.status_code in [requests.codes.ok]:
          # 最後に使った時刻を記録してチケットを保存
          ticketmanager.ticket(ticket)

        result['status_code'] = r.status_code

        result['Content-Type'] = r.headers['Content-Type']

        if r.headers['Content-Type'].find("json") >= 0:
          result['data'] = r.json()
        else:
          result['data'] = r.text

        return result
        #
      return _wrapper
    return _outer_wrapper
  #


  # デコレータ版のGET
  # requestsが必要とする引数はデコレータが**kwargsにセットしてくれる
  # この関数の戻り値はデコレータに横取りされ、加工されたものがコール元に返却される
  @set_ticket()
  def get(self, api='', params='', **kwargs):
    """apiで指定したURLにrequests.getで接続して、レスポンスを返します。"""

    api = api if api.startswith('/') else '/' + api
    url = self._prefix + "/api/" + self._version + api

    try:
      logging.info("GET '%s'", url)
      r = requests.get(url, params=params, **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_ticket()
  def post(self, api='', data='', **kwargs):
    """apiで指定したURLにrequests.postで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + "/api/" + self._version + api

    try:
      logging.info("POST '%s'", url)
      r = requests.post(url, json.dumps(data), **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_ticket()
  def put(self, api='', data='', **kwargs):
    """apiで指定したURLにrequests.putで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + "/api/" + self._version + api

    try:
      logging.info("POST '%s'", url)
      r = requests.put(url, json.dumps(data), **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_ticket()
  def delete(self, api='', **kwargs):
    """apiで指定したURLにrequests.deleteで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + "/api/" + self._version + api

    try:
      logging.info("POST '%s'", url)
      r = requests.delete(url, **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None

  #
  # 以下、getterとsetter
  #

  def protocol(self, *_):
    """URLのプロトコルの接頭語を取得、設定します"""
    if not _:
      return self._protocol
    else:
      self._protocol = _[0]
      self.setPrefix()
      return self

  def hostname(self, *_):
    """ホスト名（IPアドレス）を取得、設定します"""
    if not _:
      return self._hostname
    else:
      self._hostname = _[0]
      self.setPrefix()
      return self

  def port(self, *_):
    """ポート番号を取得、設定します"""
    if not _:
      return self._port
    else:
      self._port = _[0]
      self.setPrefix()
      return self

  def username(self, *_):
    """接続ユーザ名を取得、設定します"""
    if not _:
      return self._username
    else:
      self._username = _[0]
      return self

  def password(self, *_):
    """接続パスワードを取得、設定します"""
    if not _:
      return self._password
    else:
      self._password = _[0]
      return self

  def version(self, *_):
    """APIバージョンを取得、設定します"""
    if not _:
      return self._version
    else:
      self._version = _[0]
      return self

  def timeout(self, *_):
    """タイムアウト値（秒）を取得、設定します"""
    if not _:
      return self._timeout
    else:
      self._timeout = _[0]
      return self

  def prefix(self, *_):
    """URLのプレフィクス部を取得、設定します。hostnameとportは変更されません。"""
    if not _:
      return self._prefix
    else:
      self._prefix = _[0]
      return self

  def proxies(self, *_):
    """プロキシ設定を取得、設定します。"""
    if not _:
      return self._proxies
    else:
      self._proxies = _[0]
      return self
  #
