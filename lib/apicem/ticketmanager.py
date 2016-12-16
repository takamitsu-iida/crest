#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APIC-EMのREST API接続に必要なチケットをスレッドセーフに管理するためのモジュールです."""

import datetime
import logging
import os
import pickle
from threading import RLock


class TicketManager(object):
  """APIC-EMへの接続状態を管理します"""

  # チケットを保存するファイル名
  # pickleで保存するので中身はjsonではない。
  TICKET_FILENAME = ".ticket.pickle"

  # チケットを取得した際の応答
  # このうちの、responseキーに対応する部分をticket_jsonとして保持する
  # {
  #   "response": {
  #     "serviceTicket": "ST-7956-M9GASWAe3KSQebWHoepC-cas",
  #     "idleTimeout": 1800,
  #     "sessionTimeout": 21600 },
  #   "version": "1.0"
  # }

  # 独自に追加するキー
  KEY_PUBLISHED = "__published__"
  KEY_LAST_USED = "__last_used__"

  # 時刻表示のフォーマット
  DATE_FORMAT = "%a %b %d %H:%M:%S %Y"

  def __init__(self):
    """コンストラクタ"""
    # オンメモリのチケット
    self._ticket_json = None

    # 排他制御用のロック
    self._lock = RLock()


  def saveTicket(self, ticket):
    """チケットをpickleでファイルに保存します"""
    if not ticket:
      return

    now = datetime.datetime.now().strftime(self.DATE_FORMAT)

    # 発行時刻が記入されていないなら記入する
    if not self.KEY_PUBLISHED in ticket:
      ticket[self.KEY_PUBLISHED] = now

    # 最後に使った時刻を記入する
    ticket[self.KEY_LAST_USED] = now

    try:
      with open(self.TICKET_FILENAME, 'wb') as f:
        pickle.dump(ticket, f)
    except IOError as e:
      logging.error(e)

  def loadTicket(self):
    """pickleでファイルに保存されているチケットを復元します"""
    if not os.path.isfile(self.TICKET_FILENAME):
      return None

    try:
      with open(self.TICKET_FILENAME, 'rb') as f:
        ticket = pickle.load(f)
        return ticket
    except IOError as e:
      logging.error(e)
    except ValueError as e:
      logging.error(e)
    return None

  def isNotExpired(self, ticket):
    """有効期限が切れていないことを確認します"""
    now = datetime.datetime.now()

    # "published": "Thu Dec 08 15:52:20 2016",
    published = ticket[self.KEY_PUBLISHED]
    publishedDate = datetime.datetime.strptime(published, self.DATE_FORMAT)

    sessionTimeout = ticket["sessionTimeout"]
    expire = publishedDate + datetime.timedelta(seconds=sessionTimeout)

    # 誤差を考えて3分を減算する
    expire -= datetime.timedelta(minutes=3)

    if now < expire:
      # セッションタイムアウトの範囲内なので、こんどはアイドルタイムアウトを確認する
      lastUsedStr = ticket.get(self.KEY_LAST_USED, published)
      lastUsed = datetime.datetime.strptime(lastUsedStr, self.DATE_FORMAT)
      idleTimeout = ticket["idleTimeout"]
      expire = lastUsed + datetime.timedelta(seconds=idleTimeout)
      expire -= datetime.timedelta(minutes=3)
      # アイドルタイムアウトにも抵触していないので、エクスパイアしていない
      if now < expire:
        return True
    #
    return False

  def getTicket(self):
    """チケットを取得して返します"""
    # まずはメモリキャッシュの有無を確認して、あればそれを返却
    ticket = self._ticket_json
    if ticket and self.isNotExpired(ticket):
      logging.info("found ticket on memory cache")
      return ticket
    logging.info("there is no ticket on memory cache")

    # メモリキャッシュにない場合は、ディスクから探す
    ticket = self.loadTicket()
    if ticket and self.isNotExpired(ticket):
      logging.info("found ticket on disk cache")
      self._ticket_json = ticket
      return ticket
    logging.info("there is no ticket on disk cache")
    return None

  def lock(self):
    """ロックを獲得します"""
    self._lock.acquire()

  def release(self):
    """ロックを開放します."""
    self._lock.release()

  def ticket(self, *_):
    """チケットを取得、設定します."""
    if not _:
      return self.getTicket()
    else:
      self._ticket_json = _[0]
      self.saveTicket(_[0])
      return self

###############################################################################

#
# TicketManagerクラスのインスタンスをグローバル名前空間に一つ生成して共有する
#
ticketmanager = TicketManager()
