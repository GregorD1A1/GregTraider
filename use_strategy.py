import backtrader as bt
from strategies import RSI1
import datetime


beginning_cash = 1000

cerebro = bt.Cerebro(optreturn=False)

cerebro.addstrategy(RSI1)

data1 = bt.feeds.YahooFinanceCSVData(
    dataname='historical_data/CEZ.PR.csv',
    fromdate=datetime.datetime(2018, 1, 1),
    todate=datetime.datetime(2019, 1, 1))
cerebro.adddata(data1)

cerebro.broker.setcash(beginning_cash)
cerebro.broker.setcommission(0.002)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(bt.sizers.FixedSize, stake=1)

if __name__ == '__main__':
    cerebro.run()

    end_portfolio_value = cerebro.broker.get_value()
    zysk = (end_portfolio_value / start_portfolio_value - 1) * 100
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} %')

    cerebro.plot()
