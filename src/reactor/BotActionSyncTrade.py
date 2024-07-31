from reactor.AbstractAction import AbstractAction
from datetime import datetime
from utils.global_context import *
from model.trade_order import TradeOrder
from model.trade import Trade
from decimal import Decimal
import time
import logging

logger = logging.getLogger(__name__)

class BotActionSyncTrade(AbstractAction):
  
  def __init__(self):
    super().__init__(commands=['sync_trade'])
    
  async def _execute(self, event_body):
    # get the last sync timestamp
    syncTick = self.getSyncTick()
    now = int(round(time.time() * 1000))
    then = syncTick.trade_last_sync
    # sync all trades since last sync tick
    bfx_trades = await self.get_bfx_trades(then, now)
    trades = [Trade.from_bfx_trade(bfx_trade) for bfx_trade in bfx_trades]
    self.storage.saveObjects(trades)
