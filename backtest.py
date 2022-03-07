import backtrader
from strategies import TradingStrategy
import datetime


beginning_cash = 10000

cerebro = backtrader.Cerebro(optreturn=False)

#cerebro.addstrategy(TradingStrategy)

# Ładownie danych
data = backtrader.feeds.YahooFinanceCSVData(
    dataname='historical_data/STB.OL.csv',
    fromdate=datetime.datetime(2019, 1, 1),
    todate=datetime.datetime(2020, 1, 1))
cerebro.adddata(data)

cerebro.addanalyzer(backtrader.analyzers.SharpeRatio, _name='sharpe_ratio')
cerebro.optstrategy(TradingStrategy, pfast=range(4, 20), pslow=range(30, 70))

# Ustawiamy, ile mamy pozycji do sprawdzenia
cerebro.addsizer(backtrader.sizers.SizerFix, stake=3)
cerebro.broker.setcash(beginning_cash)
# cerebro.broker.setcommission(0.001)
start_portfolio_value = cerebro.broker.get_value()
# ustawiamy, ile akcji naraz kupujemy
cerebro.addsizer(backtrader.sizers.FixedSize, stake=100)

if __name__ == '__main__':
    optimized_runs = cerebro.run()
    
    results_list =[]
    for run in optimized_runs:
        for strategy in run:
            zysk = round(strategy.broker.get_value() - beginning_cash, 2)
            sharpe = strategy.analyzers.sharpe_ratio.get_analysis()['sharperatio']
            results_list.append([strategy.params.pfast, strategy.params.pslow, zysk, sharpe])

    sort_by_shape = sorted(results_list, key=lambda x: x[2], reverse=True)
    for record in sort_by_shape[:5]:
        print(record)

    end_portfolio_value = cerebro.broker.get_value()
    zysk = (end_portfolio_value / start_portfolio_value - 1) * 100
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} %')

    cerebro.plot()


