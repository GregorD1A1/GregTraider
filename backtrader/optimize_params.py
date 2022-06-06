import backtrader as bt
from strategies import RSI1, TrendFollowing
import datetime



beginning_cash = 100000

cerebro = bt.Cerebro(optreturn=False)

data = bt.feeds.GenericCSVData(
    dataname='historical_data/DE30_60m.csv',
    fromdate=datetime.datetime(2020, 9, 23),
    todate=datetime.datetime(2021, 3, 30),
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

cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, riskfreerate=0,  _name='sharpe_analys')
cerebro.optstrategy(TrendFollowing, stop_loss_spacing=[i/1000 for i in range(12, 25, 3)],
        peak_detection_spacing1=[i/1000 for i in range(3, 7)], peak_detection_spacing2=[i/1000 for i in range(2, 4)],
        ema_opening_price_spacing=[i/1000 for i in range(3, 7)])

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
        results_list.append([zysk, sharpe, run[0].params.stop_loss_spacing, run[0].params.peak_detection_spacing1,
                             run[0].params.peak_detection_spacing2, run[0].params.ema_opening_price_spacing])

    sort_by_shape = sorted(results_list, key=lambda x: x[0], reverse=True)
    for record in sort_by_shape[:25]:
        print(record)
