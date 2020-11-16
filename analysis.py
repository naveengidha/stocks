import yfinance as yf, pandas as pd, shutil, os, time, glob
from get_all_tickers import get_tickers as gt
from enum import Enum

class Sectors(Enum):
    NON_DURABLE_GOODS = 'Consumer Non-Durables'
    CAPITAL_GOODS = 'Capital Goods'
    HEALTH_CARE = 'Health Care'
    ENERGY = 'Energy'
    TECH = 'Technology'
    BASICS = 'Basic Industries'
    FINANCE = 'Finance'
    SERVICES = 'Consumer Services'
    UTILITIES = 'Public Utilities'
    DURABLE_GOODS = 'Consumer Durables'
    TRANSPORT = 'Transportation'


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
        
        r = (2 * pivot) - low
        s = (2 * pivot) - high
        
        return [r, s]

    except Exception as e:
        print("Error calculating S/R levels for", stock, ":", e)
        return 2 * [-1]


def get_prcntg(stock, previous_close, current):
    """
    Calculate current gain/loss % compared to yesterday close
    """
    try:
        return (((current - previous_close) / previous_close) * 100)
    except Exception as e:
        print("Error calculating open % for", stock, ":", e)
        return -1


def get_sectors():
    """
    Get sector tickers
    """

    for sector in Sectors:
        tickers = []
        tickers = gt.get_tickers_filtered(mktcap_min=500, mktcap_max=2000, sectors = sector.value)

        df = get_stock_details(tickers)
        df.to_csv("reports/" + sector.name + ".csv", index = False)

        print(df.to_string(index = False))


def get_custom():
    """
    Custom list of stocks
    """

    tickers = ["NIO", "SQ", "MRNA", "PLTR"]

    df = get_stock_details(tickers)
    print(df.to_string(index = False))


def get_stock_details(tickers):
    """
    Get stock details from tickers[] and return data frame
    API limits: 2,000/hour; 48,000/day
    """

    # variables to keep track of success/failure calls to API
    i = 0
    api_calls = 0
    failures = 0
    not_imported = 0
    results = []

    while(i < len(tickers)) and (api_calls < 1800):
        try:
            # get stock data and save to individual CSVs
            stock = tickers[i]
            ticker_obj = yf.Ticker(str(stock))
            ticker_data = ticker_obj.history(period="1mo")
            ticker_data.to_csv("CSV/"+stock+".csv")

            # get stock historical data
            stock_csv = glob.glob("CSV/"+stock+".csv")
            data = pd.read_csv(stock_csv[0])

            time.sleep(2)
        
            api_calls += 1
            failures = 0
            i += 1

            stock_SR = get_SR(stock, 
                              data.tail(2))

            # (previous close - current) / previous close = % relative to the closing price
            gain_loss = get_prcntg(stock, 
                                   data.tail(2).iloc[0,4], 
                                   data.tail(1).iloc[0,4])

            results.append([stock, 
                            round(data.tail(2).iloc[0,4], 2),
                            round(data.tail(1).iloc[0,1], 2), 
                            round(gain_loss, 2), 
                            round(data.tail(1).iloc[0,4], 2), 
                            round(stock_SR[0], 2), 
                            round(stock_SR[1], 2), 
                            f"{data.tail(1).iloc[0,5]:,}"])

            df = pd.DataFrame(results, 
                              columns = ["Stock", 
                                         "Previous close", 
                                         "Open price",
                                         "Gain/Loss %", 
                                         "Close/Current", 
                                         "Resistance", 
                                         "Support", 
                                         "Volume"])
            
        except Exception as e:
            print("Error:", e)
            if failures > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
                i+=1
                not_imported += 1
            api_calls += 1
            failures += 1

    return df

    print("API calls:", api_calls)
    print("Not imported:", not_imported)

#main
get_custom()
#get_sectors()
