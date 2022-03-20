import backtrader as bt


class RSI1(bt.Strategy):
    params = (('rsi_period', 14),)

    def log(self, text):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Kupione, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'Sprzedane, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Nie udało się zrealizować zamówienia')

        # reset zamówienia
        self.order = None

    def next(self):
        # jeśli jest otwarte zamówienie
        if self.order:
            return

        if self.rsi < 30:
            if not self.position:
                self.log(f'Kupujemy po: {self.dataclose[0]:.2f}')
                self.order = self.buy()
            # zamykamy pozycję krótką
            elif self.position.size < 0:
                self.order = self.close()

        if self.rsi > 70:
            if not self.position:
                self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
                self.order = self.sell()
            # zamykamy pozycję krótką
            elif self.position.size > 0:
                self.order = self.close()