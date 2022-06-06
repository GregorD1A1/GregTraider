import backtrader as bt
import matplotlib.pyplot as plt


class RSI1(bt.Strategy):
    params = dict(rsi_period=14, default_low_rsi_trsh=30, default_high_rsi_trsh=70,
                  rsi_low_trsh_max=60, rsi_high_trsh_min=40,
                  rsi_low_trsh_min=20, rsi_high_trsh_max=70, close_offset=10,
                  rsi_peak_detection_offset=8, ema_period=200, rsi_per_ema_angle_coeff1=100000,
                  rsi_per_ema_angle_coeff2=25000,
                  macd_trsh_trend_inverse=20, macd_sharp_correction_delay=50)

    def log(self, text):
        dt = self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0].close, period=self.params.rsi_period)
        self.ema = bt.indicators.ExponentialMovingAverage(self.datas[0].close, period=self.p.ema_period)
        self.macd = bt.indicators.MACD(self.datas[0].close, period_me1=26, period_me2=12, period_signal=9)
        self.kat_pochylenia_ema = (self.ema(0) - self.ema(-1)) / self.ema(0)
        self.kat_pochylenia_ema_smoothed = bt.indicators.MovingAverageSimple(self.kat_pochylenia_ema, period=10)
        self.kat_pochylenia_signal_macd = self.macd.signal(0) - self.macd.signal(-1)
        self.przeciecia_ema = bt.Or(bt.And(self.ema(-1) > self.data.close(-1), self.ema(0) < self.data.close(0)), \
                                    bt.And(self.ema(-1) < self.data.close(-1), self.ema(0) > self.data.close(0)))

        self.czas_transakcji = 0

        self.plot_memory_init()

    def next(self):
        self.add_data_for_plotting()
        # jeśli jest otwarte zamówienie
        if self.order:
            return

        self.if_close_long()
        self.if_close_short()
        self.if_open_long()
        self.if_open_short()

    # Otwieramy pozycję, jeśli:
    # 1. rsi jest powyżej obliczonego progu
    # 2. rsi odwraca się w przeciwnym kierunku i nowe rsi jest oddalone od poprzedniego o określony krok,
    # by wyeliminować niepewne szczytki
    # 3. minął odstęp czasowy od ostatniej transakcji
    # 4. nie jesteśmy po mocnym trendzie, po którym oczekujemy korekty (macd powyżej określonego progu
    # i jego linia sygnałowa (uśredniony macd) idzie już w przeciwnym kierunku (wyłączone dla gry 5-minutowej)

    # sprawdza, czy otwierać pozycję długą
    def if_open_long(self):
        # kupujemy na szczycie RSI
        if self.rsi.lines.rsi[-1] < self.lower_trsh() and self.rsi.lines.rsi[0] > self.rsi.lines.rsi[-1] + self.p.rsi_peak_detection_offset:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if len(self) - self.czas_transakcji > self.params.close_offset and \
                    not self.sharp_falling_correction_possible():
                self.open_long()

    # sprawdza, czy otwierać pozycję krótką
    def if_open_short(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.lines.rsi[-1] > self.upper_trsh() and self.rsi.lines.rsi[0] < self.rsi.lines.rsi[-1] - self.p.rsi_peak_detection_offset:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if len(self) - self.czas_transakcji > self.params.close_offset and \
                    not self.sharp_growing_correction_possible():
                self.open_short()

    # sprawdza, czy zamykać pozycję długą
    def if_close_long(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.lines.rsi[-1] > self.upper_trsh() and self.rsi.lines.rsi[0] < self.rsi.lines.rsi[-1]:
            # zamykamy pozycję długą
            if self.position and self.position.size > 0:
                self.close_pos()

    # sprawdza, czy zamykać pozycję krótką
    def if_close_short(self):
        # Kupujemy na szczycie RSI
        if self.rsi.lines.rsi[-1] < self.lower_trsh() and self.rsi.lines.rsi[0] > self.rsi.lines.rsi[-1]:
            # zamykamy pozycję krótką
            if self.position and self.position.size < 0:
                self.close_pos()

    def open_long(self):
        self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
        self.order = self.buy()

    def open_short(self):
        self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
        self.order = self.sell()

    def close_pos(self):
        self.order = self.close()
        self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')

    def stop(self):
        # rysujemy wykres na końcu
        self.custom_plot()

    # obliczenie progów RSI w zależności od kątu pochylenia EMA
    def upper_trsh(self):
        # górny
        if self.kat_pochylenia_ema_smoothed >= 0:
            trsh = self.p.default_high_rsi_trsh + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff2
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh > self.p.rsi_high_trsh_max: trsh = self.p.rsi_high_trsh_max
            return trsh
        # dolny
        else:
            trsh = self.p.default_high_rsi_trsh + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff1
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh < self.p.rsi_high_trsh_min: trsh = self.p.rsi_high_trsh_min
            return trsh


    def lower_trsh(self):
        # dolny
        if self.kat_pochylenia_ema_smoothed <= 0:
            trsh = self.p.default_low_rsi_trsh + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff2
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh < self.p.rsi_low_trsh_min: trsh = self.p.rsi_low_trsh_min
            return trsh
        # górny
        else:
            trsh = self.p.default_low_rsi_trsh + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff1
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh > self.p.rsi_low_trsh_max: trsh = self.p.rsi_low_trsh_max
            return trsh

    # kolejne dwie funkcje sprawdzają, czy trend nie wystrzelił ostatnio za wysoko, co może spowodować równie gwałtową
    # korektę
    def sharp_growing_correction_possible(self):
        # sprawdzamy, czy nie był macd powyżej progu przez ostatnie ileś kroków oraz czy macd już spada z powrotem
        for val in self.macd.get(size=self.p.macd_sharp_correction_delay):
            if val > self.p.macd_trsh_trend_inverse and self.kat_pochylenia_signal_macd < 0:
                return True
        return False

    def sharp_falling_correction_possible(self):
        # sprawdzamy, czy nie był macd poniżej progu przez ostatnie ileś kroków oraz czy macd już spada z powrotem
        for val in self.macd.get(size=self.p.macd_sharp_correction_delay):
            if val < -self.p.macd_trsh_trend_inverse and self.kat_pochylenia_signal_macd > 0:
                return True
        return False

    # funkcje pomocnicze, nie związane z logiką
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

    def plot_memory_init(self):
        self.plot_step = 0
        self.x_axis_mem = []
        self.upper_trsh_mem = []
        self.lower_trsh_mem = []
        self.ema_mem = []
        self.rsi_mem = []
        self.katy_ema_mem = []

    def add_data_for_plotting(self):
        self.x_axis_mem.append(self.plot_step)
        self.plot_step += 1
        self.upper_trsh_mem.append(self.upper_trsh())
        self.lower_trsh_mem.append(self.lower_trsh())
        self.ema_mem.append(self.ema[0])
        self.rsi_mem.append(self.rsi[0])
        self.katy_ema_mem.append(self.kat_pochylenia_ema_smoothed[0])

    def custom_plot(self):
        plt.subplot(311)
        plt.plot(self.x_axis_mem, self.upper_trsh_mem, self.x_axis_mem, self.lower_trsh_mem, self.x_axis_mem,
                 self.rsi_mem)
        plt.ylim([0, 100])
        plt.ylabel("RSI")
        plt.subplot(312)
        plt.ylabel("EMA")
        plt.plot(self.ema_mem)
        plt.subplot(313)
        plt.ylabel("Kąt EMA")
        plt.plot(self.katy_ema_mem)
        plt.show(block=False)
