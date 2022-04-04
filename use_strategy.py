import backtrader as bt
from strategies import RSI1, TrendFollowing
import datetime
import quantstats


beginning_cash = 200000

cerebro = bt.Cerebro(optreturn=False)

data = bt.feeds.GenericCSVData(
    dataname='historical_data/DE30_60m.csv',
    fromdate=datetime.datetime(2021, 4, 1),
    todate=datetime.datetime(2021, 11, 25),
    dtformat=('%b %d %Y %I:%M:%S %p'),
    nullvalue=0.0,
    high=4,
    low=3,
    open=2,
    close=1,
    volume=5,
    openinterest=-1,
    timeframe=bt.TimeFrame.Ticks
    )
cerebro.adddata(data)

cerebro.addstrategy(RSI1, close_offset=49)
#cerebro.addstrategy(TrendFollowing, ema_period=200, trend_detection_delay=70)   # dla WIGu
#cerebro.addstrategy(TrendFollowing, trend_detection_delay=15, stop_loss_spacing=0.024, peak_detection_price_spacing1=0.008,
#                  peak_detection_price_spacing2=0.002, ema_opening_price_spacing=0.004)

cerebro.broker.setcash(beginning_cash)
#cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(bt.sizers.FixedSize, stake=1)
# dodajemy pyfolio
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')

if __name__ == '__main__':
    results = cerebro.run()

    end_portfolio_value = cerebro.broker.get_value()
    zysk = end_portfolio_value - start_portfolio_value
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} pkt.')

    cerebro.plot()

    pyfolio_stats = results[0].analyzers.getbyname('PyFolio')
    returns, positions, transactions, groos_lev = pyfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)

    quantstats.reports.html(returns, output='stats.html', title='RSI1')