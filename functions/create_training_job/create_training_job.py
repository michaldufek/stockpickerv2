# LAMBDA -- Asynchronous Training Job
import boto3
from uuid import uuid1
import os

def create_training_job(event, context):
    # Create SageMaker client
    sagemaker = boto3.client('sagemaker')
    
    # Receive IAM Role for Lambda resource
    try:
        role_arn = os.environ['RoleArn']
    except KeyError:
        role_arn = 'arn:aws:iam::384850799342:role/service-role/AmazonSageMaker-ExecutionRole-20211014T102427'
        #print('fuckoff kamo')
        #return
    # Start the training job
    sagemaker.create_training_job(
        TrainingJobName=event['model-id'],
        AlgorithmSpecification={
            'TrainingImage': event['Image'],
            'TrainingInputMode': 'File'
        },
        RoleArn=role_arn,
        InputDataConfig=[
            {
                'ChannelName': 'train',
                'DataSource': {
                    'S3DataSource': {
                        'S3Uri': 's3://sagemaker-eu-central-1-384850799342/Storage/Model/record-io-data',
                        'S3DataType': 'S3Prefix'
                    }
                },
                #'ContentType': 'text/csv',
                #'CompressionType': 'None'
            }
        ],
        OutputDataConfig={
            'S3OutputPath': event['S3OutputPath']
        },
        ResourceConfig={
            'InstanceType': event['instanceType'],
            'InstanceCount': 1,
            'VolumeSizeInGB': 50
        },
        HyperParameters=event['hyperparameters'],
        StoppingCondition={
            'MaxRuntimeInSeconds': 3600
        }
    )

    # Wait for the training job to complete
    training_job_status = "InProgress"
    while training_job_status != "Completed" and training_job_status != "Failed":
        training_job_info = sagemaker.describe_training_job(TrainingJobName=event["model-id"])
        training_job_status = training_job_info["TrainingJobStatus"]

    # Return the status of the training job
    return {
                "TrainingJobStatus": training_job_status
            }