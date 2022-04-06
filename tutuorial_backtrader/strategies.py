import backtrader


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


class Sentiment(backtrader.Strategy):
    params = (('period', 10), ('devfactor', 1),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.sentiment = self.datas[1].close
        self.order = None
        self.log_list = []

        self.bbands = backtrader.indicators.BollingerBands(
            self.sentiment, period=self.params.period, devfactor=self.params.devfactor)

    def log(self, text):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {text}')
        self.log_list.append(f'{dt.isoformat()}, {text}')

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

        # czy wartość sentymentu jest powyżej linii górnej
        if self.sentiment[0] > self.bbands.lines.top[0] and not self.position:
            self.log(f'Sentiment Value: {self.sentiment[0]:.2f}, Top band: {self.bbands.lines.top[0]:.2f},'
                     f'Kupujemy po: {self.dataclose[0]:.2f}')
            self.order = self.buy()

        # czy wartość sentymentu jest poniżej linii dolnej
        elif self.sentiment[0] < self.bbands.lines.bot[0] and not self.position:
            self.log(f'Sentiment Value: {self.sentiment[0]:.2f}, Bottom band: {self.bbands.lines.bot[0]:.2f},'
                f'Sprzedajemy po: {self.dataclose[0]:.2f}')
            self.order = self.sell()

        # zamykamy, jeśli powyzsże warnki nie są spełnione
        else:
            if self.position:
                self.log(f'Google Sentiment Value: {self.sentiment[0]:.2f}, Bottom band: {self.bbands.lines.bot[0]:.2f},'
                         f'Top band: {self.bbands.lines.top[0]:.2f}, Zamykam pozycję po {self.dataclose[0]:.2f}')
                self.order = self.close()

    # wywołuje się na końcu
    def stop(self):
        with open('custom_sentiment_log.csv', 'w') as log_file:
            for line in self.log_list:
                log_file.write(line + '\n')
