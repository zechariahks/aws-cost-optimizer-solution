import boto3

def get_lambda_recommendations():
    client = boto3.client('compute-optimizer')
    response = client.get_lambda_function_recommendations()
    
    ssm_client = boto3.client('ssm')
    
    for recommendation in response['lambdaFunctionRecommendations']:
        function_arn = recommendation['functionArn']
        memory_size = recommendation['memorySizeRecommendationOptions'][0]['rankedOptions'][0]['memorySize']
        param_name = f"/lambda/memory/{function_arn.split(':')[-1]}"
        
        ssm_client.put_parameter(
            Name=param_name,
            Value=str(memory_size),
            Type='String',
            Overwrite=True
        )

    return {'status': 'Success'}