import backtrader
from strategies import TradingStrategy
import datetime


cerebro = backtrader.Cerebro()

cerebro.addstrategy(TradingStrategy)

# Ładownie danych
data = backtrader.feeds.YahooFinanceCSVData(
    dataname='historical_data/STB.OL.csv',
    fromdate=datetime.datetime(2018, 11, 1),
    todate=datetime.datetime(2019, 6, 1))
cerebro.adddata(data)

# Ustawiamy, ile mamy pozycji do sprawdzenia
cerebro.addsizer(backtrader.sizers.SizerFix, stake=3)

if __name__ == '__main__':
    cerebro.broker.setcash(10000)
    #cerebro.broker.setcommission(0.001)
    start_portfolio_value = cerebro.broker.get_value()
    # ustawiamy, ile akcji naraz kupujemy
    cerebro.addsizer(backtrader.sizers.FixedSize, stake=100)

    cerebro.run()


    end_portfolio_value = cerebro.broker.get_value()
    zysk = (end_portfolio_value / start_portfolio_value - 1) * 100
    print(f'Z {start_portfolio_value:.2f} pkt. zrobiliśmy {end_portfolio_value:.2f} pkt.. Zysk wynosi: {zysk:.2f} %')

    cerebro.plot()


