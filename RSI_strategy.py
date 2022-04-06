import backtrader as bt
import matplotlib.pyplot as plt


class RSI1(bt.Strategy):
    params = dict(rsi_period=14, default_lower_rsi_trsh=30, max_modified_rsi_lower_trsh=50, close_offset=10, ema_period=200,
                  rsi_per_ema_angle_coeff=50000, ema_max_angle_counter_trend_opening=0.00035,
                  macd_trsh_trend_inverse=20, macd_sharp_correction_delay=50)

    def log(self, text):
        dt = self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {text}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0].close, period=self.params.rsi_period)
        self.rsi_smoothed = bt.indicators.MovingAverageSimple(self.rsi, period=5)
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

        self.close_long()
        self.close_short()
        self.open_long()
        self.open_short()

    # Otwieramy pozycję, jeśli:
    # 1. rsi jest powyżej obliczonego progu
    # 2. rsi odwraca się w przeciwnym kierunku
    # 3. minął odstęp czasowy od ostatniej transakcji
    # 4. trend nie jest za mocny, by otwierać pozycję w tym kierunku (czyli kąt ema nie jest za duży) Przemyśleć to ząłożenie, nie działa jak należy
    # 5. nie jesteśmy po mocnym trendzie, po którym oczekujemy korekty (macd powyżej określonego progu
    # i jego linia sygnałowa (uśredniony macd) idzie już w przeciwnym kierunku
    def open_long(self):
        # kupujemy na szczycie RSI
        if self.rsi.lines.rsi[-1] < self.lower_trsh() and self.rsi.lines.rsi[0] > self.rsi.lines.rsi[-1]:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if len(self) - self.czas_transakcji > self.params.close_offset and \
                    self.kat_pochylenia_ema_smoothed > -self.p.ema_max_angle_counter_trend_opening and \
                    not self.sharp_falling_correction_possible():

                self.log(f'Kupujemy po: {self.dataclose[0]:.2f}')
                self.order = self.buy()

    def open_short(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.lines.rsi[-1] > self.upper_trsh() and self.rsi.lines.rsi[0] < self.rsi.lines.rsi[-1]:
            # by nie otwierać natychmiast po poprzedniej transakcji i nie otwierać przeciw mocnemu trendowi
            if len(self) - self.czas_transakcji > self.params.close_offset and \
                    self.kat_pochylenia_ema_smoothed < self.p.ema_max_angle_counter_trend_opening and \
                    not self.sharp_growing_correction_possible():
                self.log(f'Sprzedajemy po: {self.dataclose[0]:.2f}')
                self.order = self.sell()

    def close_long(self):
        # Sprzedajemy w dołku RSI
        if self.rsi.lines.rsi[-1] > self.upper_trsh() and self.rsi.lines.rsi[0] < self.rsi.lines.rsi[-1]:
            # zamykamy pozycję długą
            if self.position and self.position.size > 0:
                self.order = self.close()
                self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')

    def close_short(self):
        # Kupujemy na szczycie RSI
        if self.rsi.lines.rsi[-1] < self.lower_trsh() and self.rsi.lines.rsi[0] > self.rsi.lines.rsi[-1]:
            # zamykamy pozycję krótką
            if self.position and self.position.size < 0:
                self.order = self.close()
                self.log(f'Zamykamy po: {self.dataclose[0]:.2f}')

    def stop(self):
        # rysujemy wykres na końcu
        self.custom_plot()

    # obliczenie progów RSI w zależności od kątu pochylenia EMA
    def upper_trsh(self):
        if self.kat_pochylenia_ema >= 0:
            return 100 - self.p.default_lower_rsi_trsh
        else:
            trsh = (100 - self.p.default_lower_rsi_trsh) + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh < (100 - self.p.max_modified_rsi_lower_trsh): trsh = (100 - self.p.max_modified_rsi_lower_trsh)
            return trsh


    def lower_trsh(self):
        if self.kat_pochylenia_ema <= 0:
            return self.p.default_lower_rsi_trsh
        else:
            trsh = self.p.default_lower_rsi_trsh + self.kat_pochylenia_ema_smoothed * self.p.rsi_per_ema_angle_coeff
            # próg górny, by nie składał transakcji na szczytkach trendu zgodnie z trendem
            if trsh > self.p.max_modified_rsi_lower_trsh: trsh = self.p.max_modified_rsi_lower_trsh
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
        plt.subplot(312)
        plt.plot(self.ema_mem)
        plt.subplot(313)
        plt.plot(self.katy_ema_mem)
        plt.show(block=False)