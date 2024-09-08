# trade_order.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class TradeOrderStat(BaseModel):
    __tablename__ = 'trade_order_stat'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    def __init__(self, *args, **kwargs):
        self.id : int = 0
        self.account_id : int = 0
        self.user_id : int = 0
        self.symbol = None
        self.firstTradeTime = None
        self.lastTradeTime = None
        self.total_profit = 0  
        self.total_fee = 0
        self.acumulative_amount = 0
        self.acumulative_buy_amount = 0
        self.acumulative_sell_amount = 0
        self.max_buy_amount = 0
        self.max_buy_cost = 0
        self.max_sell_amount = 0
        self.max_sell_cost = 0
        self.buy_stack = []
        self.sell_stack = []
        self.count : int = 0
        self.last_oper_count : int = -1
        self.last_trade_price : Decimal = Decimal(0)
        self.buy_total_cost : Decimal = Decimal(0)
        self.buy_total_amount : Decimal = Decimal(0)
        self.buy_total_fee : Decimal = Decimal(0)
        self.buy_average_price : Decimal = Decimal(0)
        self.sell_total_cost : Decimal = Decimal(0)
        self.sell_total_amount : Decimal = Decimal(0)
        self.sell_total_fee : Decimal = Decimal(0)
        self.sell_average_price : Decimal = Decimal(0)
        self.highest_price : Decimal = Decimal(0)
        self.lowest_price : Decimal = Decimal(2**128)
        self.seconds_in_a_year = 365 * 24 * 60 * 60
        self.apr : Decimal = Decimal(0)
        self.net_profit : Decimal = Decimal(0)
        self.profit_a_year : Decimal = Decimal(0)
        self.total_deposit : Decimal = Decimal(0)
        self.impermanent_loss : Decimal = Decimal(0)
        super().__init__(*args, **kwargs)
    
    def _buy_stack_push(self, price, amount, fee):
        self.buy_stack.append((price, amount, fee))
        self.acumulative_buy_amount += amount
        self.max_buy_amount = max(self.max_buy_amount, self.acumulative_buy_amount)
        self.buy_total_cost += price * amount
        self.max_buy_cost = max(self.max_buy_cost, self.buy_total_cost)
        self.buy_total_amount += amount
        self.buy_total_fee += fee
        self.buy_average_price = self.buy_total_cost / self.buy_total_amount
        self.lowest_price = min(self.lowest_price, price)
        
        
    def _buy_stack_pop(self):
        (price, amount, fee) = self.buy_stack.pop()
        self.acumulative_buy_amount -= amount
        self.buy_total_cost -= price * amount
        self.buy_total_amount -= amount
        self.buy_total_fee -= fee
        if self.buy_total_amount > 0:
            self.buy_average_price = self.buy_total_cost / self.buy_total_amount
        else:
            self.buy_average_price = Decimal(0)
        
        return (price, amount, fee)
    
    def _sell_stack_push(self, price, amount, fee):
        self.sell_stack.append((price, amount, fee))
        self.acumulative_sell_amount += amount
        self.max_sell_amount = max(self.max_sell_amount, self.acumulative_sell_amount)
        self.sell_total_cost += price * amount
        self.max_sell_cost = max(self.max_sell_cost, self.sell_total_cost)
        self.sell_total_amount += amount
        self.sell_total_fee += fee
        self.sell_average_price = self.sell_total_cost / self.sell_total_amount
        self.highest_price = max(self.highest_price, price)

    def _sell_stack_pop(self):
        (price, amount, fee) = self.sell_stack.pop()
        self.acumulative_sell_amount -= amount
        self.sell_total_cost -= price * amount
        self.sell_total_amount -= amount
        self.sell_total_fee -= fee
        if self.sell_total_amount > 0:
            self.sell_average_price = self.sell_total_cost / self.sell_total_amount
        else:
            self.sell_average_price = Decimal(0)
        return (price, amount, fee)
    def report(self):
        return f'''
id : {self.id}
Symbol: {self.symbol}
Count: {self.count}
First Trade Time: {self.firstTradeTime}
Last Trade Time: {self.lastTradeTime}
Total Grid Profit: {self.total_profit:.2f}
Total Fees: {self.total_fee:.2f}
Fee Ratio: {self.total_fee / self.total_profit * 100 if self.total_profit != 0 else 0:.2f}%
Net Grid Profit: {self.net_profit:.2f}
Acumulative Amount: {self.acumulative_amount:.4f}
Max cost: {self.max_buy_cost + self.max_sell_cost:.2f}
Buy average price: {self.buy_average_price:.4f}
Sell average price: {self.sell_average_price:.4f}
Profit a year: {self.profit_a_year:.2f}
Impermanent Loss: {self.impermanent_loss:.2f} (Base On Last Trade)
APR: {self.apr*100:.2f}%'''
    def print(self):
        print(self.report())

    def processStack(self):
        # 如果卖出栈不为空，处理卖出操作
        while self.buy_stack and self.sell_stack:
            buy_price, buy_amount, buy_fee = self._buy_stack_pop()
            sell_price, sell_amount, sell_fee = self._sell_stack_pop()
            
            if sell_amount <= buy_amount:
                # 按比例分配费用
                fee_ratio = sell_amount / buy_amount
                adjusted_buy_fee = buy_fee * fee_ratio
                profit = (sell_price - buy_price) * sell_amount - adjusted_buy_fee - sell_fee
                self.total_profit += profit
                self.total_fee += adjusted_buy_fee + sell_fee
                buy_amount -= sell_amount
                if buy_amount > 0:
                    self._buy_stack_push(buy_price, buy_amount, buy_fee - adjusted_buy_fee)
            else:
                # 按比例分配费用
                fee_ratio = buy_amount / sell_amount
                adjusted_sell_fee = sell_fee * fee_ratio
                profit = (sell_price - buy_price) * buy_amount - buy_fee - adjusted_sell_fee
                self.total_profit += profit
                self.total_fee += buy_fee + adjusted_sell_fee
                sell_amount -= buy_amount
                if sell_amount > 0:
                    self._sell_stack_push(sell_price, sell_amount, sell_fee - adjusted_sell_fee)
    def stat(self, rows):
        for row in rows:
            if row['oper_count'] > self.last_oper_count:
                self.firstTradeTime = row['mts_update'] if self.firstTradeTime is None else min(self.firstTradeTime, row['mts_update'])
                self.lastTradeTime = row['mts_update'] if self.lastTradeTime is None else max(self.lastTradeTime, row['mts_update'])
                self.acumulative_amount += row['amount_orig']
                self.count += 1 
                if row['amount_orig'] > 0:
                    self._buy_stack_push(row['price_avg'], row['amount_orig'], row['fee'])
                elif row['amount_orig'] < 0:
                    self._sell_stack_push(row['price_avg'], -row['amount_orig'], row['fee'])                
                self.processStack()
                self.last_trade_price = row['price_avg']
                cur_value = self.acumulative_amount * self.last_trade_price
                if self.acumulative_amount>0:
                    self.impermanent_loss = cur_value - (self.buy_total_cost + self.buy_total_fee)
                else: 
                    self.impermanent_loss = (self.sell_total_cost - self.sell_total_fee) + cur_value 
                    
                if self.firstTradeTime != self.lastTradeTime:
                    elapsed_time = datetime.fromisoformat(self.lastTradeTime) - datetime.fromisoformat(self.firstTradeTime)
                    self.net_profit = self.total_profit - self.total_fee
                    self.profit_a_year = self.net_profit / Decimal(str(elapsed_time.total_seconds())) * self.seconds_in_a_year
                    self.total_deposit = self.max_buy_cost + self.max_sell_cost
                    self.apr = self.profit_a_year / self.total_deposit
                self.last_oper_count = row['oper_count']
