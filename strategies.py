import  backtrader


class TradingStrategy(backtrader.Strategy):
    params = (('pfast', 7), ('pslow', 25),)
    def __init__(self):
        self.datasclose = self.datas[0].close
        self.order = None

        self.slow_sma = backtrader.indicators.MovingAverageSimple(period=self.params.pslow)
        self.fast_sma = backtrader.indicators.MovingAverageSimple(period=self.params.pfast)


    def log(self, text):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {text}')

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
        if self.order:
            return

        # sprawdza, czy posiadamy pozycję
        if not self.position:
            # jeśli nastąpiło przebicie szybką sma wolnej w górę, to otwieramy pozycję długą
            if self.fast_sma[0] > self.slow_sma[0] and  self.fast_sma[-1] < self.slow_sma[-1]:
                self.log(f'Kupuję po {self.datasclose[0]:.2f}')
                # pilnujemy też, by drugi raz nie kupić
                self.order = self.buy()
                '''
            # jeśli nastąpiło przebicie szybką sma wolnej w dół, to otwieramy pozycję krótką
            elif self.fast_sma[0] < self.slow_sma[0] and self.fast_sma[-1] > self.slow_sma[-1]:
                self.log(f'Sprzedaję po {self.datasclose[0]:.2f}')
                # pilnujemy też, by drugi raz nie sprzedać
                self.order = self.sell(size=100)
                '''

        else:
            if self.fast_sma[0] < self.slow_sma[0] and self.fast_sma[-1] > self.slow_sma[-1]:
                self.log(f'Zamykam pozycję po {self.datasclose[0]:.2f}')
                self.order = self.close()
                '''
            # Zamykamy pozycję po 5 sesjach
            if len(self) >= (self.bar_executed + 5):
                self.log(f'Zamykam pozycję po {self.datasclose[0]:.2f}')
                self.order = self.close()
'''