from reactor.AbstractAction import AbstractAction
from model.trade_order_stat import TradeOrderStat

class BotActionTradeReport(AbstractAction):
  def __init__(self):
    super().__init__(commands=['TradeReport'])

  async def _execute(self, event_body):
    data = event_body['data']
    if type(data)==dict:
      self.buffer_message(f"json data not supported")
      return
    if len(data) == 0:
      filter_lambda = lambda Attr: Attr('account_id').eq(self.account.id)
      stats = self.storage.loadObjects(TradeOrderStat, filter_lambda)
      sorted_stats = sorted(stats, key=lambda x: x.id)
      for stat in sorted_stats:
        self.buffer_message(f"{stat.report()}")
    elif len(data) == 1:
      strategy_id = int(data[0])
      stat = self.storage.loadObjectById(TradeOrderStat, strategy_id)
      if stat and stat.account_id == self.account.id:
        self.buffer_message(f"{stat.report()}")