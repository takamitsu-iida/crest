#!/usr/bin/env python
# coding: utf-8

"""
Cisco IOS-XEのREST APIへの接続機能を提供します。
依存外部モジュール
  requests

IOS-XE側の設定はこのようになります。

参考リンク
http://www.cisco.com/c/en/us/td/docs/routers/csr1000/software/configuration/csr1000Vswcfg/RESTAPI.html

!
hostname csr1000v
!
transport-map type persistent webui https-webui
 secure-server
!
no aaa new-model
clock timezone JST 9 0
!
username cisco privilege 15 password 0 cisco
!
interface VirtualPortGroup0
 ip unnumbered GigabitEthernet2
!
virtual-service csr_mgmt
 ip shared host-interface GigabitEthernet2
 activate
!
ip http secure-server
!
transport type persistent webui input https-webui
!
ntp server 172.18.0.1
!

デバッグをかけるなら
csr1000v#debug remote-management restful-api info

タイムゾーンを設定しても、トークンの有効期限の時刻はUTCで返されるので、こちら側で対処が必要。
"""

import functools  # デコレータを作るのに必要
import json
import logging

try:
  import requests
  # HTTPSを使用した場合に、証明書関連の警告を無視する
  requests.packages.urllib3.disable_warnings()
except ImportError:
  logging.error("requestsモジュールのインポートに失敗しました。")
  exit()

try:
  from .tokenmanager import tokenmanager
except ImportError:
  logging.error("tokenmanagerモジュールのインポートに失敗しました。")
  # exit()


class RestClient(object):
  """IOS-XEのREST APIに接続するための情報を格納します."""
  # pylint: disable=too-many-instance-attributes

  def __init__(self):
    self._protocol = "https"
    self._port = 55443  # デフォルトのポート番号は55443
    self._timeout = 10
    try:
      from . import config
      self._hostname = config.hostname
      self._username = config.username  # privilege 15を持ったユーザ
      self._password = config.password  # パスワード
      self._proxies = config.proxies
    except ImportError:
      logging.info("configモジュールの読み込みに失敗しました。")
      self._hostname = ""
      self._username = ""
      self._password = ""
      self._proxies = None
    self._prefix = ""
    self.setPrefix()

  def setPrefix(self):
    """プレフィクスを作り直します"""
    if self._port == 443:
      self._prefix = "%s://%s" % (self._protocol, self._hostname)
    else:
      self._prefix = "%s://%s:%s" % (self._protocol, self._hostname, str(self._port))


  # トークンを保存するファイル名
  # pickleで保存するので中身はjsonではない。
  TOKEN_FILENAME = "crest.token"

  # 接続URL
  TOKEN_SERVICES = "/api/v1/auth/token-services"

  # 接続用トークンのオンメモリのキャッシュ
  #{
  #  "kind": "object#auth-token",
  #  "link": "https://10.35.185.11:55443/api/v1/auth/token-services/2010780488",
  #  "expiry-time": "Thu Dec 24 07:22:10 2015",
  #  "token-id": "L8W34hhAOicwHrQ4zu+LdHNeGryIUL9PhMBLUagDwf0="
  #}
  token_json = None


  def getToken(self):
    """スレッドセーフなトークン取得"""
    tokenmanager.lock()
    token = self._getToken()
    tokenmanager.release()
    return token

  def _getToken(self):
    """実際のトークン取得処理"""
    hostname = self._hostname
    token = tokenmanager.getToken(hostname=hostname)
    if token:
      return token

    logging.info("trying to get new token from ios-xe")

    # トークンを取得するための接続先
    url = self._prefix + self.TOKEN_SERVICES

    # ヘッダ
    headers = {
      'Accept': "application/json, text/plain",
      'Content-Type': "application/json"
    }

    # タイムアウト値
    timeout = self._timeout

    # プロキシ
    proxies = self._proxies

    # ベーシック認証に使う情報
    auth = (self._username, self._password)

    try:
      r = requests.post(url, headers=headers, auth=auth, timeout=timeout, proxies=proxies, verify=False)

      if r.status_code in [requests.codes.ok]:
        if r.headers['Content-Type'].find("json") >= 0:
          token = r.json()
          # チケットマネージャに保管
          tokenmanager.saveToken(self._hostname, token)
          return token
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  # 未使用・デコレータを使わない版
  # GET
  def _get(self, api):
    """apiで指定したURLにHTTP GETで接続して、レスポンスをJSONで返します。"""
    token = self.getToken()
    if not token:
      return None

    api = api if api.startswith('/') else '/' + api
    url = self._prefix + api

    timeout = self._timeout

    headers = {
      'Accept': "application/json, text/plain",
      'Content-Type': "application/json",
      'X-auth-token': token['token-id']
    }

    logging.info("GET '%s'", url)

    try:
      r = requests.get(url, timeout=timeout, headers=headers, verify=False, proxies=self._proxies)
      logging.info("status code : %s", r.status_code)
      if r.status_code in [requests.codes.ok]:
        if r.headers['Content-Type'].find("json") >= 0:
          return r.json()
        return r.text
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  # デコレータ定義
  def set_token():
    """GET/POST/PUT/DELETEの前後処理をするデコレータ"""
    def _outer_wrapper(wrapped_function):
      @functools.wraps(wrapped_function)
      def _wrapper(self, *args, **kwargs):
        #
        # 前処理
        #

        # 戻り値は必ずオブジェクトを返す
        result = {}

        # トークンを取得
        token = self.getToken()
        if not token:
          logging.error("failed to obtain token to access ios-xe rest api")
          result['status_code'] = -10
          result['data'] = None
          return result

        # ヘッダにトークンを挿入
        headers = {
          'Accept': "application/json, text/plain",
          'Content-Type': "application/json",
          'X-auth-token': token['token-id']
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
          logging.error("failed to access ios-xe rest api")
          result['status_code'] = -1
          result['data'] = None
          return result

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
  @set_token()
  def get(self, api='', params='', **kwargs):
    """apiで指定したURLにrequests.getで接続して、レスポンスを返します。"""

    api = api if api.startswith('/') else '/' + api
    url = self._prefix + api

    try:
      logging.info("GET '%s'", url)
      r = requests.get(url, params=params, **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_token()
  def post(self, api='', data='', **kwargs):
    """apiで指定したURLにrequests.postで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + api

    try:
      logging.info("POST '%s'", url)
      r = requests.post(url, json.dumps(data), **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_token()
  def put(self, api='', data='', **kwargs):
    """apiで指定したURLにrequests.putで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + api

    try:
      logging.info("POST '%s'", url)
      r = requests.put(url, json.dumps(data), **kwargs)
      return r
    except requests.exceptions.RequestException as e:
      logging.error(e)
    return None


  @set_token()
  def delete(self, api='', **kwargs):
    """apiで指定したURLにrequests.deleteで接続して、レスポンスを返します。"""
    api = api if api.startswith('/') else '/' + api
    url = self._prefix + api

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

  def timeout(self, *_):
    """タイムアウト値（秒）を取得、設定します"""
    if not _:
      return self._timeout
    else:
      self._timeout = _[0]
      return self

  def proxies(self, *_):
    """プロキシ設定を取得、設定します。"""
    if not _:
      return self._proxies
    else:
      self._proxies = _[0]
      return self
