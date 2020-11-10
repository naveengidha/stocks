import yfinance as yf, pandas as pd, shutil, os, time, glob
from get_all_tickers import get_tickers as gt


def get_OBV(stock, data):
    """
    Columns: [Date,Open,High,Low,Close,Volume,Dividends,Stock Splits]
    """

    try:
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


def get_SR(stock, data):
    """
    Calculate support and resistance levels
    Columns: [Date,Open,High,Low,Close,Volume,Dividends,Stock Splits]
    """

    try:
        high = data.iloc[0,2]
        low = data.iloc[0,3]
        close = data.iloc[0,4]
        pivot = (high + low + close) / 3
        
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        r3 = r1 + (high - low)
        s3 = s1 - (high - low)

        return [r1, s1, r2, s2, r3, s3]

    except Exception as e:
        print("Error calculating S/R levels for", stock, ":", e)
        return 6 * [-1]


# MAIN
# API limits: 2,000/hour, 48,000/day

api_calls = 0
failures = 0
not_imported = 0
i=0
results = []
tickers = gt.get_tickers_filtered(mktcap_min=150000, mktcap_max=10000000)
#tickers = ["NIO", "SQ", "TSLA", "AMD"]

while(i < len(tickers)) and (api_calls < 1800):
    try:
        # get stock data and save to individual CSVs
        stock = tickers[i]
        ticker_object = yf.Ticker(str(stock))

        # save historical data
        historical_data = ticker_object.history(period="max")
        historical_data.to_csv(stock+".csv")

        # get stock historical data
        stock_csv = glob.glob(stock+".csv")
        data = pd.read_csv(stock_csv[0])

        time.sleep(2)
        
        api_calls += 1
        failures = 0
        i += 1

        # stock OBV for last 10 trading days
        stock_obv = get_OBV(stock, data.tail(10))
        # stock S/R levels for 1 trading day
        # for multiple S/R levels, run data through for loop for N rows in data (include date)
        stock_SR = get_SR(stock, data.tail(1))

        results.append([stock, data.tail(1).iloc[0,1], stock_SR[0], stock_SR[1], stock_SR[2], stock_SR[3], stock_SR[4], stock_SR[5], data.tail(1).iloc[0,4], stock_obv])

        df = pd.DataFrame(results, columns = ["Stock", "Open", "R1", "S1", "R2", "S2", "R3", "S3", "Close/Current", "OBV"])
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

print("Processed: " + str(i - not_imported) + "/" + str(len(tickers)))

top = df.head(10)
print(top.to_string(index = False))

bottom = df.tail(10)
print(bottom.to_string(index = False))
