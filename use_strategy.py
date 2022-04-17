import backtrader as bt
from RSI_strategy import RSI1
import datetime
import quantstats


beginning_cash = 3000

cerebro = bt.Cerebro(optreturn=False)

data = bt.feeds.GenericCSVData(
    dataname='historical_data/DE30_5m.csv',
    fromdate=datetime.datetime(2022, 3, 4),
    todate=datetime.datetime(2022, 3, 20),
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

#cerebro.addstrategy(RSI1, rsi_period=14, default_lower_rsi_trsh=30, max_modified_rsi_lower_trsh=60, close_offset=10,
#                rsi_peak_detection_offset=8, ema_period=250, rsi_per_ema_angle_coeff=100000,
#                macd_trsh_trend_inverse=500, macd_sharp_correction_delay=180)   # DE30 5m
cerebro.addstrategy(RSI1, rsi_period=14, default_low_rsi_trsh=30, default_high_rsi_trsh=70,
                rsi_low_trsh_max=60, rsi_high_trsh_min=40,
                rsi_low_trsh_min=20, rsi_high_trsh_max=80, close_offset=10,
                rsi_peak_detection_offset=8, ema_period=250,
                macd_trsh_trend_inverse=500, macd_sharp_correction_delay=180)   # BRAComp 5m

cerebro.broker.setcash(beginning_cash)
#cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(bt.sizers.FixedSize, stake=1)
# dodajemy pyfolio
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, riskfreerate=0,  _name='sharpe_analys')

if __name__ == '__main__':
    results = cerebro.run()

    end_portfolio_value = cerebro.broker.get_value()
    zysk = end_portfolio_value - start_portfolio_value
    sharpe = results[0].analyzers.sharpe_analys.get_analysis()['sharperatio']
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} pkt. '
          f'Wsp. Sharpe: {sharpe}')


    pyfolio_stats = results[0].analyzers.getbyname('PyFolio')
    returns, positions, transactions, groos_lev = pyfolio_stats.get_pf_items()
    returns.index = returns.index.tz_convert(None)
    quantstats.reports.html(returns, output='stats.html', title='RSI1')

    cerebro.plot()
