import backtrader
from strategies import *
import datetime


beginning_cash = 10000

cerebro = backtrader.Cerebro(optreturn=False)

cerebro.addstrategy(ATR)

data = backtrader.feeds.YahooFinanceCSVData(
    dataname='historical_data/STB.OL.csv',
    fromdate=datetime.datetime(2019, 1, 1),
    todate=datetime.datetime(2020, 1, 1))
cerebro.adddata(data)

cerebro.broker.setcash(beginning_cash)
# cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(backtrader.sizers.FixedSize, stake=100)

if __name__ == '__main__':
    cerebro.run()

    end_portfolio_value = cerebro.broker.get_value()
    zysk = (end_portfolio_value / start_portfolio_value - 1) * 100
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} %')

    cerebro.plot()
