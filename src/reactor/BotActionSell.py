from reactor.AbstractAction import AbstractAction

class BotActionSell(AbstractAction):
  symbols_supported = ["BTCUSD",
                       "BTCUST",
                       'ETHUSD',
                       'ETHUST',
                       'SOLUSD',
                       'SOLUST',
                       "EOSUSD",
                       "EOSUST"]
  def __init__(self):
    super().__init__(commands=['sell'])

  async def _execute(self, event_body):
    data = event_body['data']
    if(len(data) < 3):
      self.buffer_message("Invalid command, please use: sell <account_name> <symbol> <amount> <price>")
      return
    symbol = data[0].upper()
    if(symbol not in self.symbols_supported):
      self.buffer_message(f"Invalid symbol, please use: {self.symbols_supported}")
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