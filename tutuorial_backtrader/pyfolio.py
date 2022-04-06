import backtrader
from strategies import *
import datetime
import pandas as pd
import quantstats


beginning_cash = 10000

cerebro = backtrader.Cerebro(optreturn=False)

cerebro.addstrategy(Sentiment)

data1 = backtrader.feeds.YahooFinanceCSVData(
    dataname='historical_data/ETH-USD.csv',
    fromdate=datetime.datetime(2018, 1, 1),
    todate=datetime.datetime(2022, 1, 1))
cerebro.adddata(data1)

data2 = backtrader.feeds.GenericCSVData(
    dataname='historical_data/ETH_GTrends.csv',
    fromdate=datetime.datetime(2018, 1, 1),
    todate=datetime.datetime(2022, 1, 1),
    nullvalue=0.0,
    dtformat=('%Y-%m-%d'),
    datetime=0,
    time=-1,
    high=-1,
    low=-1,
    open=-1,
    close=1,
    volume=-1,
    openinterest=-1,
    timeframe=backtrader.TimeFrame.Weeks)
cerebro.adddata(data2)

cerebro.addanalyzer(backtrader.analyzers.PyFolio, _name='PyFolio')

cerebro.broker.setcash(beginning_cash)
cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(backtrader.sizers.FixedSize, stake=100)

cerebro.addwriter(backtrader.WriterFile, csv=True, out='sentiment_log.csv')

if __name__ == '__main__':
    results = cerebro.run()
    strat = results[0]

    pyfolio_stats = strat.analyzers.getbyname('PyFolio')
    returns, positions, transactions, groos_lev = pyfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    transactions.to_csv('transactions.csv')

    quantstats.reports.html(returns, output='stats.html', title='Sentiment')


    end_portfolio_value = cerebro.broker.get_value()
    zysk = (end_portfolio_value / start_portfolio_value - 1) * 100
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} %')

    cerebro.plot()