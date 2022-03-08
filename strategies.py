import  backtrader


class Crossover(backtrader.Strategy):
    params = (('pfast', 5), ('pslow', 12),)
    def __init__(self):
        self.datasclose = self.datas[0].close
        self.order = None

        self.fast_sma = backtrader.indicators.MovingAverageSimple(period=self.params.pfast)
        self.slow_sma = backtrader.indicators.MovingAverageSimple(period=self.params.pslow)

        self.sma_crossover = backtrader.indicators.CrossOver(self.fast_sma, self.slow_sma)

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
            if self.sma_crossover > 0:
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
            if self.sma_crossover < 0:
                self.log(f'Zamykam pozycję po {self.datasclose[0]:.2f}')
                self.order = self.close()
                '''
            # Zamykamy pozycję po 5 sesjach
            if len(self) >= (self.bar_executed + 5):
                self.log(f'Zamykam pozycję po {self.datasclose[0]:.2f}')
                self.order = self.close()
'''

class ATR(backtrader.Strategy):
    params = (('period', 14),)
    def log(self, text):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high

    def next(self):
        range_total = 0
        for i in range(-13, 1):
            true_range = self.datahigh[i] - self.datalow[i]
            range_total += true_range
        ATR = range_total / self.params.period

        self.log(f'Close: {self.dataclose[0]:.2f}, ATR: {ATR:.4f}')

