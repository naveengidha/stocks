import yfinance as yf, pandas as pd, shutil, os, time, glob, ssl
from get_all_tickers import get_tickers as gt


def get_OBV(stock):
    """
    Columns: [Date,Open,High,Low,Close,Volume,Dividends,Stock Splits]
    """

    try:
        stock_csv = glob.glob(stock+".csv")
        data = pd.read_csv(stock_csv[0]).tail(10)
        positive = []
        negative = []
        OBV_value = 0
        count = 0
        while(count < 10):
            if data.iloc[count,1] < data.iloc[count,4]:
                positive.append(count)
            elif data.iloc[count,1] > data.iloc[count,4]:
                negative.append(count)
            count += 1

        # daily volume / opening price
        for i in positive:
            OBV_value = round(OBV_value + (data.iloc[i,5]/data.iloc[i,1]))
        for i in negative:
            OBV_value = round(OBV_value - (data.iloc[i,5]/data.iloc[i,1]))

        return OBV_value
    except Exception as e:
        print("Error calculating OBV value for", stock, ":", e)
        return -1


# MAIN
# API limits: 2,000/hour, 48,000/day

api_calls = 0
failures = 0
not_imported = 0
i=0
results = []
#tickers = gt.get_tickers_filtered(mktcap_min=15000, mktcap_max=10000000)
tickers = ["NIO","SQ"]
print("Stocks to observe: " + str(len(tickers)))    

while(i < len(tickers)) and (api_calls < 1800):
    try:
        # get stock data and save to CSVs
        stock = tickers[i]
        temp = yf.Ticker(str(stock))
        Hist_data = temp.history(period="max")
        Hist_data.to_csv(stock+".csv")
        # let Yahoo API process calls
        time.sleep(2)

        api_calls += 1
        failures = 0
        i += 1

        stock_obv = get_OBV(stock)

        results.append([stock, stock_obv])

        df = pd.DataFrame(results, columns = ["Stock", "OBV"])
        # rank by OBV
        df["Ranked"] = df["OBV"].rank(ascending = False)
        # sort ranked stocks
        df.sort_values("OBV", inplace = True, ascending = False)
        # save to CSV
        df.to_csv("DAILY_REPORT.csv", index = False)

    except ValueError:
        print("Yahoo Finance Backend Error")
        if failures > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            not_imported += 1
        api_calls += 1
        failures += 1
print("Successfully imported: " + str(i - not_imported))
