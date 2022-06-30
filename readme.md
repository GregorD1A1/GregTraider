Gregtraider is a simple framework for automated online trading and trading strategy backtesting on historical data. You can ask: "Ok, there are many libraries for strategy backtesting, why should I use Gregtraider?". Let me show you some pros of it.

Advantages of Gregtraider:
1. You should write your strategy only once. Use single strategy class for backtesting and online trading.
2. Lack of any complicated core, that obstructing debugging.
3. Nice plotly charts.
4. Easy to modificate plots and show on them anything you want.


Ecpecially first advantage is crucial for me.  For many existing frameworks you should write dedicated strategy, adjust it, after that rewrite it the way tailored for online trading, test it on demo account for some time if there no bugs appeared during rewriting to finally make it trade. Gregtraider sves you many tedeous work. You just preparing and ajusting strategy by backtesting, and it's already ready for real trading.

How to use:
To use gregtraider you need historical traiding records saved as .csv file with colum names: 'DateTime', 'Close', 'Open', 'Low', 'High', 'Volume'. I recommend you to implement "download_csv.py" file to get that data from your broker or use online_trading_APIs/xtb/download_csv.py if your broker is xtb. You also can download data from somwhere in internet (ex. Yachoo finance) and rename columns manually. Or you can use already prepared data in historical_data/ catalog, that's best option for beginners.

Next you need to write your strategy. Basically, after implementing all things related to your broker API, inventing and adjusting strategies will be all the work you will need to do.
