import yfinance as yf, pandas as pd, shutil, os, time, glob, ssl
from get_all_tickers import get_tickers as gt


# List of the stocks we are interested in analyzing. At the time of writing this, it narrows the list of stocks down to 44. If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...] 
# tickers = gt.get_tickers_filtered(mktcap_min=150000, mktcap_max=10000000)
# Check that the amount of tickers isn't more than 1800
tickers = ["SQ", "NIO"]
print("The amount of stocks chosen to observe: " + str(len(tickers)))

for t in tickers:
    stock = yf.Ticker(str(t))
    data = stock.history()
    print(t, "\n")
    print(data)
    print("\n\n")
