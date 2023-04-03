# processing.py
# LAMBDA: FEATURES CALCULATION --> Sagemaker Processing Job

import pandas as pd
import awswrangler as wr
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, Imputer
from pyspark import SparkConf
import boto3

from pyspark.sql.functions import col, log, lag, sum, asc
from pyspark.sql.window import Window

from sklearn.impute import SimpleImputer

# For testing and devel purposes
event = {
    "S3OutputPath": "s3://custom-metadata-models-dev/1ab7e703-a628-4fd8-9f07-48dfcb2ac84d/model/model-output-1ab7e703-a628-4fd8-9f07-48dfcb2ac84d",
    "userId": "1ab7e703-a628-4fd8-9f07-48dfcb2ac84d", # michal.dufek105
    "instanceType": "ml.m5.4xlarge", # user input
    "Image": "664544806723.dkr.ecr.eu-central-1.amazonaws.com/linear-learner:latest", # user input
    "hyperparameters": {
        "predictor_type": "regressor" # user input
    },
    "universe": 'sp100', # user input
    # for local development / testing purposes only -- stack has its own roles
    # arn:aws:iam::384850799342:role/service-role/AmazonSageMaker-ExecutionRole-20211014T102427
    "CustomModelExecutionRoleArn": 'arn:aws:iam::384850799342:role/service-role/AmazonSageMaker-ExecutionRole-20211014T102427',
    #'arn:aws:iam::384850799342:role/custom-ml-CustomModelExecutionRole-1H8L1F6VNLV7L', 
    "ResourceProperties": {},
    "train-period": '2016-01-01',
    "validation-period": '2019-01-01',
    "backtest-config": {
        "backtest-period": '2019-01-01',
        "number-of-stocks": 5,
        "long-only": False,
        "random-backtest": True,
        "n-simulations": 5,
    },
    "model-id": '1ab7e703-a628-4fd8-9f07-48dfcb2ac84d-sp100-linear-learner-15'
}

# Initialize s3 client and other constants
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')
company_data_bucket = 'company-data-hub'
universe = event['universe']

if event['train_period'] is not None and event['validation_period'] is not None:
    train_period = event['train_period']
    validation_period = event['validation_period']
else:
    raise ValueError('train or test period has not valid value')

'''
def get_credentials():
     Initialize acces key, secret key and session token
    sts = boto3.client('sts')
    response = sts.get_session_token(
        DurationSeconds=86400
    )
    acces_key_id = response['Credentials']['AccessKeyId']
    secret_access_key = response['Credentials']['SecretAccessKey']
    session_token = response['Credentials']['SessionToken']
    return acces_key_id, secret_access_key, session_token
'''

def get_credentials():
    session = boto3.Session()
    credentials = session.get_credentials()
    acces_key_id = credentials.access_key
    secret_access_key = credentials.secret_key
    session_token = credentials.token
    return acces_key_id, secret_access_key, session_token

def read_tickers(universe='sp100'):
    '''Read tickers from S3 Universes'''
    print('Reading tickers')
    return wr.s3.read_csv(path=f's3://{company_data_bucket}/universes/{universe}.csv', header=None).values.flatten().tolist()
    #return pd.read_csv(f's3://{company_data_bucket}/universes/{universe}.csv', header=None).values.flatten().tolist()

def calculate_features(df):
    '''Features calculation inside pyspark dataframe'''

    # Define a StringIndexer to replace string values with integer values
    stringIndexer = StringIndexer(inputCol='Symbol', outputCol='Symbol_idx')
    df = stringIndexer.fit(df).transform(df)

    # Log return
    df = df.withColumn("Log_Return", log(col("Adj_Close") / lag("Adj_Close", 1).over(Window.partitionBy("Symbol").orderBy("Date")))) # log return

    # Currency volume
    df = df.withColumn('Currency_Volume', col('Close') * col('Volume')) # currency volume

    # Currency volume sum
    horizons = [5, 10, 22, 44, 66, 126, 252, 504, 756]
    window_specs = [Window.partitionBy('Symbol').orderBy('Date').rowsBetween(-(h-1), 0) for h in horizons]
    col_names = [f'Currency_Volume_{h}' for h in horizons]

    summed_cols = [sum(col('Currency_Volume')).over(ws).alias(cn) for ws, cn in zip(window_specs, col_names)]
    df = df.select('*', *summed_cols)

    # Currency volume -- absolute and relative changes
    horizons_long = [10, 22, 44, 66, 44, 66, 126, 252, 126, 252, 504, 756, 504, 756]
    horizons_short = [5,  5,  5,  5,  22, 22, 22,  22,  66,  66,  66,  66,  252, 252] 
    horizons_pairs = list(zip(horizons_long, horizons_short))
    #horizons_pairs = [(10, 5), (22, 5), (44, 5), (66, 5), (44, 22), (66, 22), (126, 22), (252, 22), (126, 66), (252, 66), (504, 66), (756, 66), (504, 252), (756, 252)]

    for hlong, hshort in horizons_pairs:
        col_long = f"Currency_Volume_{hlong}"
        col_short = f"Currency_Volume_{hshort}"
        col_abs = f"Currency_Volume_Absolute_Chng_{hshort}-{hlong}"
        col_rel = f"Currency_Volume_Relative_Chng_{hshort}-{hlong}"
        df = df.withColumn(col_long + '_avg', col(col_long) / hlong)
        df = df.withColumn(col_short + "_avg", col(col_short) / hshort)
        df = df.withColumn(col_abs, col(col_short) - col(col_long))
        df = df.withColumn(col_rel, col(col_short + "_avg") / col(col_long + "_avg"))

    # Drop helper columns 
    avg_cols = [f"Currency_Volume_{h}_avg" for h, _ in horizons_pairs]
    drop_cols = avg_cols + ['Currency_Volume_5_avg', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
    df = df.drop(*drop_cols)

    # Move the 'Log_Return' column to be the first column of the DataFrame
    df = df.select('Log_Return', *[col for col in df.columns if col != 'Log_Return'])
    return df

def _save_grouped_data(pdf):
    '''User-defined-function for vectorized symbol-specific features saving'''
    symbol = pdf.Symbol[0] # separate ticker to get name label
    #pdf.to_csv(f'features/{symbol}.csv', index=False)
    #wr.s3.to_csv(df=pdf, path=f's3://{company_data_bucket}/features/{symbol}.csv', index=False) # for s3
    wr.s3.to_csv(df=pdf, path=f's3://{company_data_bucket}/features/{symbol}.csv', index=False)
    return pdf

def minmax(pdf):
    '''User-defined-function for vectorized crosssectional MinMax scaling'''
    scaled = (pdf.iloc[:, 3:] - pdf.iloc[:, 3:].min()) / (pdf.iloc[:, 3:].max() - pdf.iloc[:, 3:].min())
    out = pd.concat([pdf.iloc[:, :3], scaled], axis='columns')
    return out

def split_dataset(normalized_df, train_period, validation_period):
    '''Split nnormalized data into train/validation/test period'''
    train_df = normalized_df.filter(col('Date') < train_period)
    validation_df = normalized_df.filter((col('Date') >= train_period) & (col('Date') < validation_period))
    test_df = normalized_df.filter(col('Date') >= validation_period)
    # Order dataframes by 'Date'
    sorted_train_df = train_df.orderBy(asc('Date'))
    sorted_validation_df = validation_df.orderBy(asc('Date'))
    sorted_test_df = test_df.orderBy(asc('Date'))
    return sorted_train_df, sorted_validation_df, sorted_test_df

def impute_missing_values(pdf):
    excluded_cols = ['Date', 'Symbol']
    cols = pdf.columns
    fill_cols = list( set(cols) - set(excluded_cols) )
    to_impute = pdf.loc[:, fill_cols]
    # Create an instance of SimpleImpter and specify the strategy for filling in missing values
    imputer = SimpleImputer(strategy='mean')
    # Fit the imputer to the data
    imputer.fit(to_impute)
    # Transform the DataFrame by filling in the missing DataFrame
    pdf_imputed = pd.DataFrame(imputer.transform(to_impute), columns=fill_cols)
    out = pd.concat([pdf.loc[:, excluded_cols], pdf_imputed], axis='columns')
    return out

def save_market_data(market_data):
    '''Save Market Data for Utilization in Backtest'''
    path = f'{event["S3OutputPath"]}/{event["model-id"]}/backtest'
    print('**************************************************')
    print(path)
    print('**************************************************')

    wr.s3.to_csv(market_data, f'{path}/market_data.csv', index_label='Index')

def save_captions(column_names):
    '''Save Pyspark DataFrame captions to a separate file on S3'''
    with open('/tmp/captions.txt', 'w') as f:
        f.write(','.join(column_names))

    s3_resource.meta.client.upload_file('/tmp/captions.txt', 'data-for-training', 'captions.txt')

#########################
# Features Calculation
#########################
#Initialize acces key, secret key and session token
acces_key_id, secret_access_key, session_token = get_credentials()

# https://davidlindelof.com/reading-s3-data-from-a-local-pyspark-session/
conf = SparkConf()
conf.set('spark.jars.packages', 'org.apache.hadoop:hadoop-aws:3.2.2') #https://stackoverflow.com/questions/71059267/when-writing-parquet-files-to-s3-nosuchmethoderror-void-org-apache-hadoop-util
conf.set('spark.hadoop.fs.s3a.aws.credentials.provider', 'org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider')
conf.set('spark.hadoop.fs.s3a.access.key', acces_key_id)
conf.set('spark.hadoop.fs.s3a.secret.key', secret_access_key)
conf.set('spark.hadoop.fs.s3a.session.token', session_token)
#https://spot.io/blog/improve-apache-spark-performance-with-the-s3-magic-committer/
conf.set('spark.hadoop.mapreduce.outputcommiter.factory.scheme.s3a', 'org.apache.hadoop.fs.s3a.commit.S3ACommiterFactory')
conf.set('spark.hadoop.fs.s3a.commiter.magic.enabled', 'true')
conf.set("spark.hadoop.mapreduce.fileoutputcommitter.marksuccessfuljobs", "false")

spark = SparkSession.builder.appName('LargeDataProcessing').master("local[*]").config(conf=conf).getOrCreate()
#spark.conf.set("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider")

tickers = read_tickers(universe)
price_paths = [ f's3a://{company_data_bucket}/prices/{ticker}.csv' for ticker in tickers ] # for s3 paths
df = spark.read.option('header', 'true').option('inferSchema', 'true').csv(price_paths)
df = calculate_features(df)
df_filled = df.groupBy('Symbol').applyInPandas(impute_missing_values, schema=df.schema).orderBy('Date', 'Symbol')

# Save Market Data (Log_Return, Date and Symbols) for Utilization in Backtest 
market_data = df_filled.select(['Log_Return', 'Date', 'Symbol']).filter(df_filled['Date'] >= validation_period).toPandas()
save_market_data(market_data)

# Save Pyspark DataFrame captions to a separate file on S3
save_captions(column_names=df_filled.columns)

# Save features specifically to each own file
ndf = df_filled.groupBy('Symbol').applyInPandas(_save_grouped_data, schema=df_filled.schema).count()

#########################
# Features Normalization
#########################
normalized_df = df_filled.groupBy('Date').applyInPandas(minmax, schema=df_filled.schema) # vectorized Min-Max scaling

# Drop non-numeric values
normalized_df = normalized_df.drop('Date', 'Symbol')

# Split normalized data
train_df, validation_df, test_df = split_dataset(normalized_df, train_period, validation_period)
#train_df.write.format('csv').option('header', 'true').mode('overwrite').save('train')
train_df.write.format('csv').option('header', 'false').mode('overwrite').save('s3a://data-for-training/train')
validation_df.write.format('csv').option('header', 'false').mode('overwrite').save('s3a://data-for-training/validation')
test_df.write.format('csv').option('header', 'false').mode('overwrite').save('s3a://data-for-training/test')

# EoF