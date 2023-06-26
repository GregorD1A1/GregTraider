Gregtraider is a user-friendly framework designed for automated online trading and trading strategy backtesting using historical data. Unlike many other strategy backtesting libraries, Gregtraider offers several unique advantages that make it an attractive option for traders.

## Advantages of Gregtraider:
1. Write your strategy only once: Gregtraider allows you to use a single strategy class for both backtesting and online trading, saving you time and effort.
2. No complex core: Gregtraider is designed without any complicated core components, making it easier to debug and understand.
3. Attractive plotly charts: Visualize your data using nice and clean plotly charts.
4. Easy customization: Modify plots easily and display any information you want.

The primary benefit of using Gregtraider is that you only need to write and adjust your trading strategy once for backtesting, and it is immediately ready for real trading. This saves you the tedious work of rewriting and testing your strategy multiple times.

To start using Gregtraider, you'll need historical trading records saved as a .csv file with columns named 'DateTime', 'Close', 'Open', 'Low', 'High', and 'Volume'. You can obtain this data from your broker by implementing a "download_csv.py" file or using online_trading_APIs/xtb/download_csv.py if your broker is XTB. Alternatively, you can download data from sources such as Yahoo Finance and manually rename columns, or use the pre-compiled data in the historical_data/ catalog, which is an excellent option for beginners.

Once you've acquired the necessary historical data, your primary task will be to write and implement your trading strategy. After setting up your broker API, creating and adjusting strategies will be the main focus of your work.

In summary, Gregtraider streamlines the process of online trading and strategy backtesting by allowing you to write your strategy only once, offering a simple core for easy debugging, and providing visually appealing plotly charts. Give Gregtraider a try, and you'll find it an invaluable tool for your trading ventures.
