from reactor.AbstractAction import AbstractAction

class BotActionBuy(AbstractAction):
  symbols_supported = ["BTCUSD",
                      "BTCUST",
                      'ETHUSD',
                      'ETHUST',
                      'SOLUSD',
                      'SOLUST',
                      "EOSUSD",
                      "EOSUST",
                      'USTUSD']
  def __init__(self):
    super().__init__(commands=['buy'])

  async def _execute(self, event_body):
    command = event_body['command']
    data = event_body['data']
    if(len(data) < 3):
      self.buffer_message("Invalid command, please use: buy <account_name> <symbol> <amount> <price>")
      return
    symbol = data[0].upper()
    
    if(symbol not in self.symbols_supported):
      self.buffer_message("Invalid symbol, please use: BTCUSD BTCUST USTUSD ETH2X:USD ETHUSD EOSUSD or SOLUSD")
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

    await self.buy(symbol, amount, price)