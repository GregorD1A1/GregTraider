import backtrader as bt
from strategies import RSI1, TrendFollowing
import datetime



beginning_cash = 100000

cerebro = bt.Cerebro(optreturn=False)

data = bt.feeds.GenericCSVData(
    dataname='historical_data/DE30_60m.csv',
    fromdate=datetime.datetime(2021, 9, 23),
    todate=datetime.datetime(2022, 3, 30),
    dtformat=('%b %d %Y %I:%M:%S %p'),
    nullvalue=0.0,

    high = 4,
    low = 3,
    open = 2,
    close = 1,
    volume = 5,
    openinterest = -1,
    timeframe=bt.TimeFrame.Ticks
    )

cerebro.adddata(data)

cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, riskfreerate=0,  _name='sharpe_analys')
cerebro.optstrategy(RSI1, ema_period=range(70, 321, 10), trend_detection_delay=(26, 56, 2))

# Ustawiamy, ile mamy pozycji do sprawdzenia
cerebro.addsizer(bt.sizers.FixedSize, stake=1)
cerebro.broker.setcash(beginning_cash)
# cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()

if __name__ == '__main__':
    optimized_runs = cerebro.run()

    results_list =[]
    for run in optimized_runs:
        zysk = round(run[0].broker.get_value() - beginning_cash, 2)
        sharpe = run[0].analyzers.sharpe_analys.get_analysis()['sharperatio']
        if sharpe is None:
            sharpe = 0
        results_list.append([zysk, sharpe, run[0].params.ema_period, run[0].params.trend_detection_delay])

    sort_by_shape = sorted(results_list, key=lambda x: x[0], reverse=True)
    for record in sort_by_shape[:10]:
        print(record)
