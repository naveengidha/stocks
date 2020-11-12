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


def get_open(stock, previous_close, current_open):
    """
    Calculate opening %
    """
    try:
        return (((current_open - previous_close) / previous_close) * 100)
    except Exception as e:
        print("Error calculating open % for", stock, ":", e)
        return -1


def get_stock_details():
    """
    Main loop
    API limits: 2,000/hour; 48,000/day
    """

    # variables to keep track of success/failure calls to API
    api_calls = 0
    failures = 0
    not_imported = 0

    for sector in Sectors:
        results = []
        i = 0
        tickers = gt.get_biggest_n_tickers(20, sectors = sector.value)
        while(i < len(tickers)) and (api_calls < 1800):
            try:
                # get stock data and save to individual CSVs
                stock = tickers[i]
                ticker_obj = yf.Ticker(str(stock))
                ticker_data = ticker_obj.history(period="3mo")
                ticker_data.to_csv(stock+".csv")

                # get stock historical data
                stock_csv = glob.glob(stock+".csv")
                data = pd.read_csv(stock_csv[0])

                time.sleep(2)
        
                api_calls += 1
                failures = 0
                i += 1

                stock_SR = get_SR(stock, 
                                  data.tail(2))

                open_pcntg = get_open(stock, 
                                      data.tail(2).iloc[0,4], 
                                      data.tail(1).iloc[0,1])

                if not ticker_obj.info['trailingEps']:
                    trailingEPS = -1
                else:
                    trailingEPS = round(float(ticker_obj.info['trailingEps']), 2)

                if not ticker_obj.info['forwardEps']:
                    forwardEPS = -1
                else:
                    forwardEPS = round(float(ticker_obj.info['forwardEps']), 2)

                trailingPE = round(data.tail(1).iloc[0,4] / trailingEPS, 2)

                if not ticker_obj.info['forwardPE']:
                    forwardPE = -1
                else:
                    forwardPE = round(float(ticker_obj.info['forwardPE']), 2)

                results.append([stock, 
                                round(data.tail(2).iloc[0,4], 2),
                                round(data.tail(1).iloc[0,1], 2), 
                                round(open_pcntg, 2), 
                                round(data.tail(1).iloc[0,4], 2), 
                                round(stock_SR[0], 2), 
                                round(stock_SR[1], 2), 
                                f"{ticker_obj.info['marketCap']:,}", 
                                f"{data.tail(1).iloc[0,5]:,}"])

                df = pd.DataFrame(results, 
                                  columns = ["Stock", 
                                             "Previous close", 
                                             "Open price",
                                             "Open %", 
                                             "Close/Current", 
                                             "Resistance", 
                                             "Support", 
                                             "Market cap", 
                                             "Volume"])
            
                df.sort_values("Market cap", inplace = True, ascending = False)
                df.to_csv("reports/" + sector.name + ".csv", index = False)
            except Exception as e:
                print("Error:", e)
                if failures > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
                    i+=1
                    not_imported += 1
                api_calls += 1
                failures += 1

        print(sector.name)
        print(df.to_string(index = False))

#main
get_stock_details()
