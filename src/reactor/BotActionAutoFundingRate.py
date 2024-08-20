from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.lending_plan import LendingPlan
import math
import pandas as pd
import time
from decimal import Decimal

class BotActionAutoFundingRate(AbstractAction):
  
  def __init__(self):
    super().__init__(commands=['AutoFundingRate'])

  async def _execute(self, context):
      data = context['data']
      
      lps = self.getActiveLendingPlans()
      self.buffer_message(f"Auto Setting Funding Plan Rate:")
      for lp in lps:
        await self._autoSetFundingRate(lp)
  
  async def _autoSetFundingRate(self, lp):
    now = int(round(time.time() * 1000))
    candles = await self.bfx.rest.get_public_candles(f"{lp.symbol}:p{lp.period}", 0, now, tf='1D',limit=lp.days)

    df = pd.DataFrame(candles[:-1], columns=['mts', 'open', 'close','high','low','volume'])

    high_mean = df['high'].mean()
    
    start_rate = high_mean * 100 * float(lp.low_rate)
    end_rate = high_mean * 100 * float(lp.high_rate)
    lp.start_rate = Decimal(str(start_rate))
    lp.end_rate = Decimal(str(end_rate))
    lp.rate_gap = Decimal('0')
    self.storage.saveObject(lp)
    self.buffer_message(f"  id: {lp.id}, {lp.symbol} P: {lp.period} SR: {lp.start_rate:.5f}, ER: {lp.end_rate:.5f}, RG: {lp.rate_gap:.5f} by {lp.days} days")
    
  def getActiveLendingPlans(self):
    filter_lambda = lambda Attr: Attr('status').eq('ACTIVE') & Attr('account_id').eq(self.account.id) & Attr('auto_update').eq(1)
    lps = self.storage.loadObjects(LendingPlan, filter_lambda) 
    return lps