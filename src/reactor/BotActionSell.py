from reactor.AbstractAction import AbstractAction

class BotActionSell(AbstractAction):
  def __init__(self):
    super().__init__(commands=['sell'])

  async def _execute(self, event_body):
    data = event_body['data']
    if(len(data) < 3):
      self.buffer_message("Invalid command, please use: sell <account_name> <symbol> <amount> <price>")
      return
    symbol = data[0].upper()
    if(symbol != "BTCUSD" and symbol != "BTCUST" and symbol != 'ETH2X:USD'  and symbol!='ETHUSD' and symbol!='SOLUSD'  and symbol!="EOSUSD"):
      self.buffer_message("Invalid symbol, please use: BTCUSD BTCUST ETH2X:USD ETHUSD EOSUSD or SOLUSD")
      return
    symbol = "t" + symbol
    
    #try to convert data[1] to float, if fail send error message
    amount = 0
    try:
      amount = float(data[1])
    except Exception as e:
      self.buffer_message(f"Invalid amount: {data[1]}")
      return
    
    price = 0
    try:
      price = float(data[2])
    except Exception as e:
      self.buffer_message(f"Invalid price: {data[2]}")    
      return

    await self.sell(symbol, amount, price)