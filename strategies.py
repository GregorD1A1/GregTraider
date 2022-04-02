import backtrader as bt


class RSI1(bt.Strategy):
    params = dict(rsi_period=14, upper_rsi_trsh=70, lower_rsi_trsh=30, close_offset=14, ema_period=200,
                  trend_detection_delay=70)

    def log(self, text):
        dt = self.datas[0].datetime.datetime(0)
        #print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0].close, period=self.params.rsi_period)
        self.rsi_dolek = self.rsi(0) > self.rsi(-1)
        self.prev_rsi_over_upper_trsh = self.rsi(-1) > self.params.upper_rsi_trsh
        self.prev_rsi_under_lower_trsh = self.rsi(-1) < self.params.lower_rsi_trsh

        self.ema = bt.indicators.ExponentialMovingAverage(self.datas[0].close, period=self.p.ema_period)
        self.kat_pochylenia_ema = (self.ema(0) - self.ema(-1)) / self.ema(0)

        self.przeciecia_ema = bt.Or(bt.And(self.ema(-1) > self.data.close(-1), self.ema(0) < self.data.close(0)), \
                                    bt.And(self.ema(-1) < self.data.close(-1), self.ema(0) > self.data.close(0)))

        self.czas_transakcji = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'Kupione, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'Sprzedane, {order.executed.price:.2f}')
            self.czas_transakcji = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Nie udało się zrealizować zamówienia')

        # reset zamówienia
        self.order = None

    def next(self):
        # jeśli jest otwarte zamówienie
        if self.order:
            return

        self.w_tredzie = True
        for val in self.przeciecia_ema.get(size=self.p.trend_detection_delay):
            if val:
                self.w_tredzie = False


        # zamykamy pozycję po okresie close_offset
        #if self.position:
        #    if len(self) - self.czas_transakcji > self.params.close_offset:
        #        self.order = self.close()

        # kupujemy na szczycie RSI
        if self.prev_rsi_under_lower_trsh and self.rsi.lines.rsi[0] > self.rsi.lines.rsi[-1]:
            # zamykamy pozycję krótką
            if self.position and self.position.size < 0:
                self.order = self.close()
            # otwieramy pozycje
            if len(self) - self.czas_transakcji > self.params.close_offset:
                self.log(f'Kupujemy po: {self.dataclose[0]:.2f}')
                self.order = self.buy()


        elif self.prev_rsi_over_upper_trsh and self.rsi.lines.rsi[0] < self.rsi.lines.rsi[-1]:
            # zamykamy pozycję długą
            if self.position and self.position.size > 0:
                self.order = self.close()
            # otwieramy pozycje
            if len(self) - self.czas_transakcji > self.params.close_offset:
                self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
                self.order = self.sell()



class TrendFollowing(bt.Strategy):
    params = dict(ema_period=200, trend_detection_delay=70, stop_loss_odstep=0.015)

    def log(self, text):
        dt = self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.stop_loss_padl_w_tym_trendzie = False
        self.ema = bt.indicators.ExponentialMovingAverage(self.datas[0].close, period=self.p.ema_period)
        self.przeciecia_ema = bt.Or(bt.And(self.ema(-1) > self.data.close(-1), self.ema(0) < self.data.close(0)), \
                                    bt.And(self.ema(-1) < self.data.close(-1), self.ema(0) > self.data.close(0)))
        #self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0].close, period=14)
        #self.roc = bt.indicators.RateOfChange(self.datas[0].close, period=200)
        self.peak = bt.And(self.dataclose(0) < self.dataclose(-1), self.dataclose(-1) > self.dataclose(-2))
        self.bottom = bt.And(self.dataclose(0) > self.dataclose(-1), self.dataclose(-1) < self.dataclose(-2))



    def next(self):
        self.trend_identification()
        self.position_opening()
        self.close_position_when_ema_crosses_price()
        self.stoploss_caliculation_and_activation()

    def stoploss_caliculation_and_activation(self):
        # jeśli obecna pozycja długa
        if self.position and self.position.size > 0:
            if self.dataclose[0] > self.peak:
               self.peak = self.dataclose[0]
            # aktywacja stoplossu
            elif self.dataclose[0] < (1 - self.p.stop_loss_odstep) * self.peak:
                self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')
                self.order = self.close()
                self.stop_loss_padl_w_tym_trendzie = True
        # jeśli obecna pozycja krótka
        elif self.position and self.position.size < 0:
            if self.dataclose[0] < self.peak:
                self.peak = self.dataclose[0]
               # aktywacja stoplossu
            elif self.dataclose[0] > (1 + self.p.stop_loss_odstep) * self.peak:
                self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')
                self.order = self.close()
                self.stop_loss_padl_w_tym_trendzie = True

    def trend_identification(self):
        self.w_tredzie = True
        for val in self.przeciecia_ema.get(size=self.p.trend_detection_delay):
            if val:
                self.w_tredzie = False
                self.stop_loss_padl_w_tym_trendzie = False

    def position_opening(self):
        if not self.position and self.w_tredzie and not self.stop_loss_padl_w_tym_trendzie:
            if self.bottom and self.dataclose[0] > self.ema[0]:
                self.log(f'Kupujemy po: {self.dataclose[0]:.2f}')
                self.order = self.buy()
            elif self.peak and self.dataclose[0] < self.ema[0]:
                self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
                self.order = self.sell()
            # przypisujemy wartość szczytu (do obliczenia stoplosu) jako początkową wartość zamówienia
            self.peak = self.dataclose[0]

    def close_position_when_ema_crosses_price(self):
        # zamykamy, jeśli ema przetnie się z ceną
        if self.position and not self.w_tredzie:
            self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')
            self.order = self.close()

