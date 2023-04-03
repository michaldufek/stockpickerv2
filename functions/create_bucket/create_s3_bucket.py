# LAMBDA: Create custom bucket
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_model_id(event, client):
    ''' Set up validate training job name '''
    list_training_jobs = client.list_training_jobs(
        NameContains=f'{event["userId"]}-{event["universe"]}-{event["Image"].split("aws.com/")[1].split(":")[0]}'
    )['TrainingJobSummaries']

    # Receive serial number (as index) for the new training job
    i = len(list_training_jobs)

    # Collect new model identification
    model_id = f'{event["userId"]}-{event["universe"]}-{event["Image"].split("aws.com/")[1].split(":")[0]}-{i}'
    
    return model_id

def create_s3_bucket(event, context):
    # Initialize S3 client and get bucket name
    s3 = boto3.client('s3', region_name='eu-central-1')
    sagemaker = boto3.client("sagemaker")
    user_id = event['userId']
    bucket_name = 'custom-metadata-models-dev'
    output_key = f'{user_id}/model/model-output-{user_id}/'
    
    try:
        # Check if the specified bucket exists
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        if bucket_name in buckets:
            print(f'Bucket {bucket_name} already exists')
            logger.info(f'Bucket {bucket_name} already exists')
        else:
            # Create S3 bucket
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
                                    'LocationConstraint': 'eu-central-1'
                    })
            print(f'Bucket {bucket_name} created')
            logger.info(f'Bucket {bucket_name} created')

        # Check if the key (folder) already exists in the S3 bucket
        response = s3.list_objects(Bucket=bucket_name, Prefix=output_key)
        if 'Contents' in response:
            # Key (folder) already exists
            print(f'Folder {output_key} already exists')
            logger.info(f'Folder {output_key} already exists')
        else:
            # Create the key (folder) in S3 bucket
            s3.put_object(Bucket=bucket_name, Key=output_key)
            print(f'Folder {output_key} created.')
            logger.info(f'Bucket {bucket_name} already exists')
                
    except Exception as e:
        logger.info(f'Exeption occured during creating custom bucket for metada and model storing: {output_key} in {bucket_name}')
    
    # Add event information for next procedures
    event['bucket_ready'] = True
    event['S3OutputPath'] = f's3://{bucket_name}/{output_key}' # path for generated data
    event['model-id'] = get_model_id(event, sagemaker)
    event['ResourceProperties']['userId'] = event['userId'] # might be to deprecation

    return event