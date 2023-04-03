# LAMBDA for Firing Sagemaker PROCESSING Job (Features calculation, normalization, missing imputation saving on S3)
from sagemaker.processing import ScriptProcessor

def lambda_handler(event, context):
    role = 'arn:aws:iam::384850799342:role/service-role/AmazonSageMaker-ExecutionRole-20211014T102427'
    processing_image_uri = '384850799342.dkr.ecr.eu-central-1.amazonaws.com/processing-image:latest'
    
    script_processor = ScriptProcessor(command=['python3'],
                                       image_uri=processing_image_uri,
                                       role=role,
                                       instance_count=1,
                                       instance_type='ml.m5.2xlarge')
    
    script_processor.run(code='./processing/processing.py')
    
    return {
        'statusCode': 200,
        'body': 'SageMaker processing job submitted successfully'
    }
