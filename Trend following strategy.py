import backtrader as bt
import matplotlib.pyplot as plt


# Do dopracowania: 1) By strategia nic nie robiła w okresie konsolidacji
# 2) By w przypadku aktywacji stoplossu a kontynuacji trendu robiła nowy zakup
class TrendFollowing(bt.Strategy):
    params = dict(ema_period=350, trend_detection_delay=10, stop_loss_spacing=0.02, peak_detection_price_spacing1=0.005,
                  peak_detection_time_spacing1=20, peak_detection_price_spacing2=0.003, ema_opening_price_spacing=0.005)

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
        # szczyt jest, jeśli teraz jest niżej niż krok wstecz, a wtedy było wyżej o określony odstęp niż trzy kroki wstecz od tamtego momentu
        #self.my_peak = bt.And(self.data.high(0) < self.data.high(-1),
        #                   self.data.high(-1) > self.data.high(-4) * (1 + self.p.peak_detection_spacing))
        #self.my_bottom = bt.And(self.data.low(0) > self.data.low(-1),
        #                     self.data.low(-1) < self.data.low(-4) * (1 - self.p.peak_detection_spacing))



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
            elif self.dataclose[0] < (1 - self.p.stop_loss_spacing) * self.peak:
                self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')
                self.order = self.close()
                self.stop_loss_padl_w_tym_trendzie = True
        # jeśli obecna pozycja krótka
        elif self.position and self.position.size < 0:
            if self.dataclose[0] < self.peak:
                self.peak = self.dataclose[0]
               # aktywacja stoplossu
            elif self.dataclose[0] > (1 + self.p.stop_loss_spacing) * self.peak:
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
        # rozważamy otwarcie pozycji, jeśli:
        # 1. już jej nie mamy; 2. jesteśmy w trendzie; 3. w tym trendzie nie zadziałał stop-loss (wątpliwe założenie,
        # coś z tym zrobić)
        if not self.position and self.w_tredzie and not self.stop_loss_padl_w_tym_trendzie:
            # jeśli zaliczamy właśnie dołek (korekta) i jesteśmy nad średnią, otwieramy pozycję długą
            if self.dataclose[0] > self.ema[0] * (1 + self.p.ema_opening_price_spacing) and self.dolek():
                self.log(f'Kupujemy po: {self.dataclose[0]:.2f}')
                self.order = self.buy()
                # przypisujemy wartość szczytu (do obliczenia stoplosu) jako początkową wartość zamówienia
                self.peak = self.dataclose[0]
            # jeśli zaliczamy właśnie szczyt (korekta) i jesteśmy pod średnią, otwieramy pozycję krótką
            elif self.dataclose[0] < self.ema[0] * (1 - self.p.ema_opening_price_spacing) and self.szczytek():
                self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
                self.order = self.sell()
                # przypisujemy wartość szczytu (do obliczenia stoplosu) jako początkową wartość zamówienia
                self.peak = self.dataclose[0]

    def close_position_when_ema_crosses_price(self):
        # zamykamy, jeśli ema przetnie się z ceną
        if self.position and not self.w_tredzie:
            self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')
            self.order = self.close()

    def szczytek(self):
        # jeśli zbocze opadające jest w ciągu dwóch iteracji opadnie o odpowiednią wartość:
        for i in range(-2, -1):
            if self.data.high[0] < self.data.high[i] * (1 - self.p.peak_detection_price_spacing2):
                # jeśli zbocze narastające w ciągu kilku iteracji narośnie o odpowiednią wartość:
                for j in range(-self.p.peak_detection_time_spacing1, -1):
                    if self.data.high[i+j] < self.data.high[i] * (1 - self.p.peak_detection_price_spacing1):
                        return True
        return False

    def dolek(self):
        # jeśli zbocze opadające jest w ciągu dwóch iteracji opadnie o odpowiednią wartość:
        for i in range(-2, -1):
            if self.data.low[0] > self.data.low[i] * (1 + self.p.peak_detection_price_spacing2):
                # jeśli zbocze narastające w ciągu kilku iteracji narośnie o odpowiednią wartość:
                for j in range(-self.p.peak_detection_time_spacing1, -1):
                    if self.data.low[i+j] > self.data.low[i] * (1 + self.p.peak_detection_price_spacing1):
                        return True
        return False
