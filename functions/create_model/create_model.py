# LAMBDA -- Create MODEL
import boto3
from uuid import uuid1

def create_model(event, context):
    # Create a boto3 sagemaker client
    sagemaker = boto3.client('sagemaker')
    iam = boto3.client('iam')
    execution_role_arn = iam.get_role(RoleName="CustomModelExecutionRole")["Role"]["Arn"]

    # Get training job
    training_job = sagemaker.describe_training_job(TrainingJobName=event['model-id'])

    # Extract the model artifact url
    model_artifacts_url = training_job['ModelArtifacts']['S3ModelArtifacts']

    # Create the model
    model_name = event["model-id"]
    sagemaker.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': event['Image'], # not neccessary the same image (GPU x CPU etc.)
            'ModelDataUrl': model_artifacts_url,
        },
        ExecutionRoleArn=execution_role_arn
    )

    return event