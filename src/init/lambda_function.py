import os
from utils.storage import Storage
from utils.sqs import SqsUtils
from model.account import Account
from model.order_grid_strategy import OrderGridStrategy
from model.trade_order import TradeOrder
from model.trade_order_history import TradeOrderHistory
from model.lending_plan import LendingPlan
from model.sync_tick import SyncTick
from model.funding_offer import FundingOffer
from model.trade import Trade
from model.trade_order_stat import TradeOrderStat

def init_table():
  storage = Storage()
  storage.createTableByCls(Account)
  storage.createTableByCls(TradeOrder)
  storage.createTableByCls(TradeOrderHistory)
  storage.createTableByCls(LendingPlan)
  storage.createTableByCls(OrderGridStrategy)
  storage.createTableByCls(SyncTick)
  storage.createTableByCls(Trade)
  storage.createTableByCls(FundingOffer)
  storage.createTableByCls(TradeOrderStat)
  
def lambda_handler(event, context):
  init_table()
  return "The sqs queue and dynomadb tables have inited success"