import boto3

def create_endpoint(event, context):
    # Create a boto3 client
    sagemaker = boto3.client('sagemaker')

    # Extract the userId from the event data
    user_id = event['ResourceProperties']['userId']

    # Generate name for model, config and endpoint
    model_name = event["model-id"]
    endpoint_name = event["model-id"]
    endpointconfig_name = event["model-id"]
    
    # Create an endpoint config
    sagemaker.create_endpoint_config(
        EndpointConfigName=endpointconfig_name,
        ProductionVariants=[
            {
                'VariantName': 'endpointConfig',
                'ModelName': model_name,
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.t2.medium',
            }
        ]
    )

    # Create the endpoint config
    sagemaker.create_endpoint(EndpointName=endpoint_name, EndpointConfigName=endpointconfig_name)
    
    # Return the endpoint name as the physical ID
    return endpoint_name