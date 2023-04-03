# LAMBDA: Backtester
from sklearn.utils import shuffle
import pandas as pd
import numpy as np
import awswrangler as wr

# User Inputs Management
backtest_config = event['backtest-config']
backtest_path = f'{event["S3OutputPath"]}{event["model-id"]}/backtest'
is_simulation = event['backtest-config']['random-backtest'] 

# Data for Backtesting Management
predictions = wr.s3.read_csv('s3://data-for-training/backtest/', header=None)
#market_data = df_filled.select(['Log_Return', 'Date', 'Symbol']).filter(df_filled['Date'] > validation_period).toPandas()
market_data = wr.s3.read_csv(f'{backtest_path}/market_data.csv', index_col='Index')
rebalances = pd.concat([market_data, predictions], axis='columns')
rebalances.columns = ['Log_Return', 'Date', 'Symbol', 'Score']

def make_backtest(pdf:pd.DataFrame, number_of_stocks=20, random_backtest=False) -> pd.DataFrame:
    '''Backtest Right?'''
    rebalance = pdf.sort_values(by='Score', ascending=False) if not random_backtest else shuffle(pdf) # shuffling in random simulation
    longs = rebalance.iloc[:number_of_stocks, :]
    shorts = rebalance.iloc[-number_of_stocks:, :]
    longs_returns = longs.Log_Return.mean()
    shorts_returns = shorts.Log_Return.mean()
    result = pd.DataFrame({'Date': [pdf.Date.iloc[0]],
                        'Longs': [longs_returns],
                        'Shorts': [shorts_returns],
                        'LongShort': [longs_returns - shorts_returns]
                        })
    return result

# Results Processing
def _calculate_metrics(equity_curves:pd.DataFrame) -> pd.DataFrame:
    print('calculating metrics... ')
    ec_without_date = equity_curves.drop('Date', axis='columns')
    metrics = pd.DataFrame({
        'Final-Equity': ec_without_date.iloc[-1],
        'Volatility': ec_without_date.std(),
        'Sharpe': (ec_without_date.iloc[-1, :] - 1) / ec_without_date.std() 
    }).T.reset_index(names='Metrics')
    
    return pd.DataFrame(metrics)

def proces_results(backtest_data:pd.DataFrame) -> pd.DataFrame: 
    '''Calculate Metrics and Equity Curves for Stockpicking'''
    long_only = np.cumprod(np.exp(backtest_data.Longs)) # np.exp converts log returns to simple returns
    long_the_short = np.cumprod(np.exp(backtest_data.Shorts))
    long_short = np.cumprod(np.exp(backtest_data.LongShort))

    equity_curves = pd.DataFrame({
        'Date': backtest_data.Date,
        'LongOnly': long_only,
        'LongTheShort': long_the_short,
        'LongShort': long_short,
    })
    
    # Calculate Metrics
    metrics = _calculate_metrics(equity_curves) # in future replace next metrics calculation

    return metrics, equity_curves

# Results Management
def save_results(metrics, equity, prefix='real'):
    # Saving Metrics
    print('saving results...')
    wr.s3.to_csv(metrics, f'{backtest_path}/{prefix}_metrics.csv')
    wr.s3.to_csv(equity, f'{backtest_path}/{prefix}_equity.csv')

def run_simulation(n_simulations, rebalances_for_backtest, number_of_stocks):
    all_equities = pd.DataFrame()
    all_metrics = pd.DataFrame()

    for i in range(n_simulations):
        random_backtest_data = rebalances_for_backtest.groupby(by='Date', as_index=False).apply(make_backtest, **{
            'number_of_stocks': number_of_stocks,
            'random_backtest': True
        })
        random_backtest_data = random_backtest_data.reset_index(drop=True)
        one_run_metrics, one_run_equity = proces_results(random_backtest_data)
        one_run_metrics['Simulation'] = i + 1
        one_run_equity['Simulation'] = i + 1
        all_metrics = pd.concat([all_metrics, one_run_metrics])
        all_equities = pd.concat([all_equities, one_run_equity])

    average_metrics = all_metrics.drop('Simulation', axis='columns').groupby('Metrics').mean(numeric_only=True).reset_index()

    return average_metrics, all_equities

# Run
rebalances_for_backtest = rebalances.loc[rebalances.Date >= backtest_config['backtest-period']]

# Real Stock-picker Predictions Evaluation
backtest_data = rebalances_for_backtest.groupby(by='Date', as_index=False).apply(make_backtest, (backtest_config['number-of-stocks']))
backtest_data = backtest_data.reset_index(drop=True)
metrics, equity = proces_results(backtest_data)
save_results(metrics, equity)

# Run Simulation: Random Picks for Benchmarking
if is_simulation:
    simul_metrics, simul_equity = run_simulation(
                                        n_simulations=backtest_config['n-simulations'], 
                                        rebalances_for_backtest=rebalances_for_backtest, 
                                        number_of_stocks=backtest_config['number-of-stocks']
                                    )
    save_results(simul_metrics, simul_equity, prefix='simul')