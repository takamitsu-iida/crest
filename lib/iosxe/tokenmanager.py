#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""IOS-XEのREST API接続に必要なトークンをスレッドセーフに管理するためのモジュールです."""

import datetime
import logging
import os
import pickle
from threading import RLock


class TokenManager(object):
  """IOS-XEのトークンを管理します"""

  # トークンを保存するファイル名
  # pickleで保存するので中身はjsonではない。
  TOKEN_FILENAME = ".token.pickle"

  # 時刻表示のフォーマット
  DATE_FORMAT = "%a %b %d %H:%M:%S %Y"

  def __init__(self):
    """コンストラクタ"""
    # オンメモリで保持しているトークンの入れ物
    self._tokens = {}

    # 排他制御用のロック
    self._lock = RLock()


  def saveToken(self, hostname="", token=None):
    """トークンをpickleでファイルに保存します"""
    if not hostname or not token:
      return

    self._tokens[hostname] = token

    try:
      with open(self.TOKEN_FILENAME, 'wb') as f:
        pickle.dump(self._tokens, f)
    except IOError as e:
      logging.error(e)


  def loadToken(self):
    """pickleでファイルに保存されているトークンを復元します"""
    if not os.path.isfile(self.TOKEN_FILENAME):
      return None

    try:
      with open(self.TOKEN_FILENAME, 'rb') as f:
        tokens = pickle.load(f)
        return tokens
    except IOError as e:
      logging.error(e)
    except ValueError as e:
      logging.error(e)
    return None

  def isNotExpired(self, token):
    """有効期限が切れていないことを確認します"""
    # expiry-time : "Thu Dec 24 07:22:10 2015"
    # これはUTC
    expire = datetime.datetime.strptime(token["expiry-time"], self.DATE_FORMAT)

    # quick hack
    # JSTにいるものと仮定して+9時間を加算する
    expire += datetime.timedelta(hours=9)

    # 誤差を考えて3分を減算する
    expire -= datetime.timedelta(minutes=3)

    # 現在時刻と比較
    now = datetime.datetime.now()
    if expire > now:
      return True
    #
    return False


  def getToken(self, hostname=""):
    """トークンを取得して返します"""
    # まずはメモリキャッシュの有無を確認して、あればそれを返却
    token = self._tokens.get(hostname, None)
    if token and self.isNotExpired(token):
      logging.info("found token on memory cache")
      return token
    logging.info("there is no token on memory cache")

    # メモリキャッシュにない場合は、ディスクから探す
    tokens = self.loadToken()
    if not tokens:
      return None

    token = tokens.get(hostname, None)
    if token and self.isNotExpired(token):
      logging.info("found token on disk cache")
      self._tokens[hostname] = token
      return token
    logging.info("there is no token on disk cache")
    return None

  def lock(self):
    """ロックを獲得します"""
    self._lock.acquire()

  def release(self):
    """ロックを開放します."""
    self._lock.release()

###############################################################################

#
# TokenManagerクラスのインスタンスをグローバル名前空間に一つ生成して共有する
#
tokenmanager = TokenManager()
