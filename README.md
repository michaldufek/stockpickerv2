StockPicker-v2: Financial Research Software for Cross-Sectional Normalization and Long-Short Equity Strategies
1. Introduction
StockPicker2 is a financial research software designed to provide a comprehensive platform for the evaluation of stocks based on multi-factor asset pricing theory and long-short equity strategies. The application ranks stocks relative to their universe mean, identifying the highest growth potential stocks to the most overvalued ones. Users can leverage this information to design a long-short portfolio, with the flexibility to customize the model based on several critical parameters.
2. Service value proposition
StockPicker2 is a versatile financial research software that empowers users to make informed decisions in designing long-short equity portfolios. The application offers a wide range of customization options, including stock universe selection, choice of machine learning algorithms, and advanced parameters for model training and backtesting. With a modular backend architecture, StockPicker2 ensures efficient daily operations, custom machine learning model training, and seamless integration with live trading platforms.
3. Key Features
3.1. Stock Universe Selection 
Users can select from a variety of stock universes such as S&P100, S&P500, Russell3000, specific sectors, or create a custom universe based on user preferences.
3.2. Machine Learning Algorithm 
Users can choose from multiple machine learning algorithms, including linear learners, neural networks, and deep reinforcement learning.
3.3. Advanced Parameters 
Users can further customize the model by defining the training, validation, and testing period, the instance type used for training, and the backtest configuration.
4. Application Architecture – Overview
The application's backend can be divided into four logical parts: Cold Start Stack, Daily Task Stack, Custom Machine Learning Stack, and Live Trading Stack.
4.1. Cold Start Stack
The Cold Start Stack sets up all necessary resources, such as buckets, keys, models, and others, for the regular operation of the application.
4.2. Daily Task Stack
The Daily Task Stack performs everyday tasks, including data harvesting, feature calculation, features scaling, data saving and retrieval, model deployment, inference, and model deletion.
4.3. Custom Machine Learning Stack
Sharing common resources with the Daily Task Stack, the Custom Machine Learning Stack focuses on the following tasks:
    • Data transformation (Min-Max and Standard Scaling)
    • Model training
    • Bulk prediction (In AWS SageMaker, this is called a Transform Job)
    • Backtest procedure to evaluate not only the machine learning performance of the model but also the business logic layer, offering more intuitive and representative performance metrics/results
4.4. Live Trading Stack The Live Trading Stack is responsible for:
    • Connecting to broker APIs such as Alpaca, Robin Hood, Interactive Brokers, XTB, and others
    • Executing approved rebalances: deployed models make inferences every day and notify users, who can either accept or deny the execution of the rebalance
5. Application Architecture – Detail Description
5.1. Download Prices
Lambda Function Name: download_prices.py 
Function Description:
This AWS Lambda function downloads stock price data from Yahoo Finance, processes it, and stores it in an S3 bucket. This version introduces a cache location for yfinance time zones and a few other changes.
Key Components:
    1. Libraries and Services:
        ◦ yfinance: Downloading stock data from Yahoo Finance
        ◦ boto3: Interacting with AWS services, specifically S3
        ◦ awswrangler: Reading and writing data to S3
    2. Input Parameters:
        ◦ event: Standard Lambda event parameter (not used in this version)
        ◦ context: Standard Lambda context parameter (not used in this function)
    3. Main Functions:
       a. read_tickers(universe='sp100'):
        ◦ Reads the tickers from S3 universes (default is 'sp100')
        ◦ Returns a list of tickers
       b. _save(pdf):
        ◦ Takes a Pandas DataFrame (pdf) as input
        ◦ Extracts the ticker symbol from the DataFrame
        ◦ Saves the DataFrame as a CSV file in the 'prices' folder in the S3 bucket without index
       c. save_price_data(data):
        ◦ Takes the downloaded price data as input
        ◦ Transforms the data into a long format with 'Date' and 'Symbol' columns, renaming 'Adj Close' to 'Adj_Close'
        ◦ Groups the data by 'Symbol
Lambda Entry Point:
        ◦ lambda_handler(event, context):
            ▪ Hardcodes the 'universe' value as 'ru3k' (commented out the event-based assignment)
            ▪ Calls read_tickers() to get the list of tickers for the specified universe
            ▪ Downloads price data for the first 750 tickers using yf.download() with progress disabled and auto_adjust set to False
            ▪ Calls save_price_data() to process and store the price data in the S3 bucket
            ▪ Returns the string 'done' upon successful completion
Output:
    • The Lambda function saves the downloaded stock price data as individual CSV files in the 'prices' folder within the specified S3 bucket, with each file named by the corresponding ticker symbol. The index is not included in the saved CSV files.
5.2. Calculate Features and Process
Lambda Function Name: processing.py
Function Description:
This Lambda function reads stock data from S3, calculates various features, normalizes the data, imputes missing values, splits the dataset into training, validation, and testing sets, and 	then saves the data back to S3.
Key Components:
    4. Libraries and Services:
        ◦ pandas
        ◦ awswrangler 
        ◦ pyspark 
        ◦ boto3 
        ◦ sklearn.impute.SimpleImputer
    5. Input Parameters:
        ◦ event: a dictionary containing various configuration details for the feature calculation 
    6. Main Functions:
            ▪ read_tickers: reads tickers from S3 Universes 
            ▪ calculate_features: calculates various features using pyspark 
            ▪ _save_grouped_data: saves features for each symbol to a separate file in S3 
            ▪ minmax: applies Min-Max scaling across each date 
            ▪ split_dataset: splits the dataset into training, validation, and testing sets 
            ▪ impute_missing_values: imputes missing values in the dataset 
            ▪ save_market_data: saves market data for utilization in backtest 
              save_captions: saves DataFrame column captions to a separate file on S3
Lambda Entry Point:
            ▪ The script (refetence: AWS Sagemaker processing job: https://docs.aws.amazon.com/sagemaker/latest/dg/use-spark-processing-container.html)
Output:
    • Processed Stock Data: The Lambda function saves the processed stock data, including the calculated features, normalized values, and imputed missing values, to separate files in the specified S3 bucket. 
    • Training, Validation, and Testing Sets: The Lambda function saves the training, validation, and testing datasets as separate CSV files in the specified S3 bucket. 
    • Market Data: The Lambda function saves the market data, which will be utilized in the backtest, to a separate file in the specified S3 bucket.
    • Captions: The Lambda function saves the DataFrame column captions (column names) to a separate file in the specified S3 bucket. This helps in understanding the structure of the processed data and for future reference.
Create S3 Buckets
Lambda Function Name: create_s3_bucket.py
Function Description:
This AWS Lambda function creates a custom S3 bucket and folder for storing metadata and model outputs. If the specified bucket and folder already exist, it logs the information and proceeds with the given bucket and folder.
Key Components:
    7. Libraries and Services:
        ◦ boto3: AWS SDK for Python, used for interacting with AWS services such as S3 and SageMaker 
        ◦ logging: Standard Python logging library for log management 
        ◦ uuid: Python module for generating unique identifiers
    8. Input Parameters:
        ◦ event: An AWS Lambda event object containing the userId, universe, and Image information
    9. Main Functions:
    • get_model_id: Generates a unique model ID for the new training job 
    • create_s3_bucket: Creates a custom S3 bucket and folder for metadata and model outputs
Lambda Entry Point:
            ▪ create_s3_bucket(event, context)
Output:
    • Bucket Created: If the specified bucket does not exist, the function creates the bucket with the given name. 
    • Folder Created: If the specified folder does not exist in the S3 bucket, the function creates the folder with the given key.
    • Event Information Updated: The function updates the 'event' dictionary with 'bucket_ready', 'S3OutputPath', 'model-id', and 'ResourceProperties' keys, which will be used in subsequent procedures.
5.3. Create Training Job
Lambda Function Name: create_training_job.py
Function Description:
This AWS Lambda function creates an asynchronous SageMaker training job using the provided event information, such as the model ID, image, instance type, and hyperparameters. It configures the input and output data sources, resource configurations, and stopping conditions for the training job.
Key Components:
    10. Libraries and Services:
        ◦ boto3: AWS SDK for Python, used for interacting with AWS services such as SageMaker 
        ◦ uuid: Python module for generating unique identifiers 
        ◦ os: Python module for interacting with the operating system, used to access environment variables
    11. Input Parameters:
        ◦ event: An AWS Lambda event object containing the model-id, Image, instanceType, and hyperparameters, among other information
        ◦ context: An AWS Lambda context object, not used in this function
    12. Main Functions:
    • create_training_job: Creates an asynchronous SageMaker training job using the provided event information
Lambda Entry Point:
            ▪ create_training_job(event, context)
Output:
    • Training Job Created: The function creates a SageMaker training job with the specified name, input data, output data, resource configuration, and hyperparameters. 
    • Event Information Updated: The function updates the 'event' dictionary with the 'TrainingJobName' key, which will be used in subsequent procedures.
5.4. Create Model
Lambda Function Name: create_model.py
Function Description:
This AWS Lambda function creates a SageMaker model using the provided event information, such as the model ID, image, and custom model execution role ARN. It first retrieves the specified training job and extracts the model artifacts URL, then creates the model with the specified name, image, and model data.
Key Components:
    13. Libraries and Services:
        ◦ boto3: AWS SDK for Python, used for interacting with AWS services such as SageMaker
    14. Input Parameters:
        ◦ event: An AWS Lambda event object containing the TrainingJobName, model-id, Image, and CustomModelExecutionRoleArn, among other information 
        ◦ context: An AWS Lambda context object, not used in this function
    15. Main Functions:
    • create_model: Creates a SageMaker model using the specified training job, model ID, image, and custom model execution role ARN
Lambda Entry Point:
            ▪ create_model(event, context)
Output:
    • Model Created: The function creates a SageMaker model with the specified name, image, and model data URL. 
    • Event Information Updated: The function updates the 'event' dictionary with the 'model-name' key, which will be used in subsequent procedures.
5.5. Create Endpoint and Config
Lambda Function Name: create_endpoint_and_config.py
Function Description:
This AWS Lambda function creates a SageMaker endpoint configuration and an endpoint itself using the provided event information. The function first generates names for the model, config, and endpoint, then creates the endpoint configuration and the endpoint using the SageMaker client.
Key Components:
    16. Libraries and Services:
        ◦ boto3: AWS SDK for Python, used for interacting with AWS services such as SageMaker
    17. Input Parameters:
        ◦ event: An AWS Lambda event object containing the model ID and other information 
        ◦ context: An AWS Lambda context object, not used in this function
    18. Main Functions:
    • create_endpoint_and_config: Creates a SageMaker endpoint configuration and an endpoint itself using the specified model ID
Lambda Entry Point:
            ▪ create_endpoint_and_config(event, context)
Output:
    • Endpoint Configuration Created: The function creates a SageMaker endpoint configuration with the specified name and production variants. 
    • Endpoint Created: The function creates a SageMaker endpoint with the specified name and endpoint configuration name. • Endpoint Name as Physical ID: The function returns the endpoint name as a physical ID.
5.6. Create transform Job (bulk prediction)
Lambda Function Name: create_transform_job.py
Function Description:
This AWS Lambda function creates a SageMaker batch transform job using Boto3. It first generates a unique batch transform job name and sets the input and output locations. The function then creates a transform job configuration and initiates the transform job using the SageMaker client.
Key Components:
    19. Libraries and Services:
        ◦ boto3: AWS SDK for Python, used for interacting with AWS services such as SageMaker
    20. Input Parameters:
        ◦ event: An AWS Lambda event object containing the model ID and other information 
        ◦ context: An AWS Lambda context object, not used in this function
    21. Main Functions:
    • get_batch_transform_id: Generates a unique batch transform job name using the provided event information ◦ create_transform_job: Creates a SageMaker batch transform job using the specified model name, input and output locations, and transform job configuration
Lambda Entry Point:
            ▪ create_transform_job(event, context)
Output:
    • Transform Job Created: The function creates a SageMaker batch transform job using the specified model name, input and output locations, and transform job configuration.

5.7. Backtester
Lambda Function Name: backtester.py
Function Description:
This AWS Lambda function performs backtesting on the predictions obtained from a trained machine learning model. It uses a user-defined configuration and market data to simulate different scenarios and calculate performance metrics such as Sharpe ratio and volatility.
Key Components:
    22. Libraries and Services:
        ◦ pandas, 
        ◦ numpy, 
        ◦ awswrangler: Used for data manipulation and storage
    23. Input Parameters:
        ◦ event: An AWS Lambda event object containing backtest configuration, S3OutputPath, and other relevant information
        ◦ context: An AWS Lambda context object, not used in this function
    24. Main Functions:
    • make_backtest: Performs backtesting on the predictions based on the provided configuration
        ◦ _calculate_metrics: Calculates performance metrics such as final equity, volatility, and Sharpe ratio
        ◦ proces_results: Processes the backtest data to generate metrics and equity curves
        ◦ save_results: Saves the calculated metrics and equity curves to S3
        ◦ run_simulation: Runs a simulation for a specified number of iterations, calculating metrics and equity curves for random stock picks
        ◦ Lambda handler: Coordinates the entire backtesting process by calling the necessary functions and managing results
       
Lambda Entry Point:
            ▪ backtester(event, context)
Output:
    • The function saves the metrics and equity curves of the real stock-picker predictions and the simulation results (if requested) to the specified S3 location
5.8. Create ‘admin’ Buckets during Cold Start
Lambda Function Name: create_admin_bucket.py
Function Description:
This AWS Lambda function creates an S3 structure consisting of three S3 buckets and their respective folder structures for storing company data, training data, and custom metadata models in a development environment.
Key Components:
    25. Libraries and Services:
        ◦ boto3, logging: Used for AWS S3 operations and logging
    26. Input Parameters:
        ◦ bucket_names: A list of bucket names to be created
        ◦ FOLDERS_COMPANY_DATA_HUB: A list of folders to be created in the 'company-data-hub' bucket
        ◦ FOLDERS_DATA_FOR_TRAINING: A list of folders to be created in the 'data-for-training' bucket
    27. Main Functions:
    • create_s3_structure: Creates the specified S3 buckets if they do not exist, and creates the folder structures inside the 'company-data-hub' and 'data-for-training' buckets
Lambda Entry Point:
            ▪ create_admin_bucket(event, context)
Output:
    • The function creates the specified S3 buckets and their folder structures if they do not already exist, and logs the results