# NEW GEN: LAMBDA: download_prices.py

import yfinance as yf
import boto3
import awswrangler as wr

s3 = boto3.client('s3')
bucket = 'company-data-hub'

yf.set_tz_cache_location('/tmp/.cache/py-yfinance')

def read_tickers(universe='sp100'):
    '''Read tickers from S3 Universes'''
    return wr.s3.read_csv(path=f's3://{bucket}/universes/{universe}.csv', header=None).values.flatten().tolist()

def _save(pdf):
    '''Private Function for Vectorized Saving Price Data'''
    ticker = pdf.Symbol.unique()[0]
    wr.s3.to_csv(df=pdf, path=f's3://{bucket}/prices/{ticker}.csv', index=False)

def save_price_data(data):
    df = data.stack(level=1).reset_index(names=['Date', 'Symbol']).rename(columns={'Adj Close': 'Adj_Close'})
    df.groupby('Symbol').apply(_save)

def lambda_handler(event, context):
    '''Lambda Entrypoint: Download Price  Data from Yahoo'''
    #universe = event['universe'] if event['universe'] is not None else 'sp100'
    universe = 'sp100'
    tickers = read_tickers(universe=universe)
    data = yf.download(tickers[:750], start='1990-01-01', progress=False, auto_adjust=False)
    save_price_data(data)
    return 'done'