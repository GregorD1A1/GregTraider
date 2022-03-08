import backtrader
from strategies import TradingStrategy
import datetime
import os


class Screener(backtrader.Analyzer):
    params = (('period', 20), ('devfactor', 2),)

    def start(self):
        self.bollinger_bands = {data: backtrader.indicators.BollingerBands(data, period=self.params.period,
                                    devfactor=self.params.devfactor) for data in self.datas}

    def stop(self):
        self.rets['over'] = []
        self.rets['under'] = []

        for data, band in self.bollinger_bands.items():
            node = data._name, data.close[0], round(band.lines.bot[0], 2)
            if data > band.lines.bot:
                self.rets['over'].append(node)
            else:
                self.rets['under'].append(node)


beginning_cash = 10000

cerebro = backtrader.Cerebro()

for ticker in os.listdir('historical_data'):
    data = backtrader.feeds.YahooFinanceCSVData(
        dataname=f'historical_data/{ticker}',
        fromdate=datetime.datetime(2017, 1, 1),
        todate=datetime.datetime(2020, 1, 1))
    cerebro.adddata(data)

cerebro.addanalyzer(Screener)

if __name__ == '__main__':
    cerebro.run(runonce=False, stdstats=False, writer=True)
