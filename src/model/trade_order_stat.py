# trade_order.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class TradeOrderStat(BaseModel):
    __tablename__ = 'trade_order'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id : int = 0 # the same as OrderGridStrategy id
    account_id : int = 0
    user_id : int = 0  # telegram user id
    symbol : None
    firstTradeTime = None
    lastTradeTime = None
    total_profit = 0
    total_fee = 0
    acumulative_amount = 0
    acumulative_buy_amount = 0
    acumulative_sell_amount = 0
    max_buy_amount = 0
    max_sell_amount = 0
    buy_stack = []
    sell_stack = []
    count : int = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _buy_stack_push(self, price, amount, fee):
        self.buy_stack.append((price, amount, fee))
        self.acumulative_buy_amount += amount
        
        
    def _buy_stack_pop(self):
        (price, amount, fee) = self.buy_stack.pop()
        self.acumulative_buy_amount -= amount
        return (price, amount, fee)
    
    def _sell_stack_push(self, price, amount, fee):
        self.sell_stack.append((price, amount, fee))
        self.acumulative_sell_amount += amount

        
    def _sell_stack_pop(self):
        (price, amount, fee) = self.sell_stack.pop()
        self.acumulative_sell_amount -= amount
        return (price, amount, fee)
    
    def print(self):
        print("Count:", self.count)
        print("First Trade Time:", self.firstTradeTime)
        print("Last Trade Time:", self.lastTradeTime)
        print("Total Grid Profit:", self.total_profit)
        print("Total Fees:", self.total_fee)
        print("Acumulative Amount:", self.acumulative_amount)
        print("Acumulative Buy Amount:", self.acumulative_buy_amount)
        print("Acumulative Sell Amount:", self.acumulative_sell_amount)
        print("Max Buy Amount :", self.max_buy_amount)
        print("Max Sell Amount:", self.max_sell_amount)
        print("Fee Ratio:", self.total_fee / self.total_profit if self.total_profit != 0 else 0)
        print("buy average:", self._buy_average_price())
        print("sell average:", self._sell_average_price())
    def _apr(self):
        start = datetime.fromisoformat(self.firstTradeTime)
        end = datetime.fromisoformat(self.lastTradeTime)
        elapsed_time = end - start
        net_profit = self.total_profit - self.total_fee
        seconds_in_a_year = 365 * 24 * 60 * 60
        profit_a_year = net_profit / Decimal(str(elapsed_time.total_seconds())) * seconds_in_a_year
        buy_price, fee  = self._buy_average_price()
        sell_price, fee  = self._sell_average_price()
        average_price = buy_price + sell_price
        total_deposit = (self.max_buy_amount +  self.max_sell_amount) * average_price
        apr = profit_a_year / total_deposit
        print("profit_a_year:", profit_a_year)
        print("apr:", apr)
        
    def _buy_average_price(self):
        if self.buy_stack:
            total_cost : Decimal = Decimal(0)
            total_amount : Decimal= Decimal(0)
            total_fee : Decimal = Decimal(0)
            for price, amount, fee in self.buy_stack:
                total_cost += price * amount
                total_amount += amount
                total_fee += fee
            return (total_cost/total_amount, total_fee)
        return (0,0)
    
    def _sell_average_price(self):
        if self.sell_stack:
            total_cost : Decimal = Decimal(0)
            total_amount : Decimal= Decimal(0)
            total_fee : Decimal = Decimal(0)
            for price, amount, fee in self.sell_stack:
                total_cost += price * amount
                total_amount += amount
                total_fee += fee
            return (total_cost/total_amount, total_fee)        
        return (0,0)
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
            self.firstTradeTime = row['mts_update'] if self.firstTradeTime is None else min(self.firstTradeTime, row['mts_update'])
            self.lastTradeTime = row['mts_update'] if self.lastTradeTime is None else max(self.lastTradeTime, row['mts_update'])
            self.acumulative_amount += row['amount_orig']
            self.count += 1 
            if row['amount_orig'] > 0:
                self._buy_stack_push(row['price_avg'], row['amount_orig'], row['fee'])
            elif row['amount_orig'] < 0:
                self._sell_stack_push(row['price_avg'], -row['amount_orig'], row['fee'])                
                
            self.processStack()

            self.max_buy_amount = max(self.max_buy_amount, self.acumulative_buy_amount)
            self.max_sell_amount = max(self.max_sell_amount, self.acumulative_sell_amount)
