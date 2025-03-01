import boto3

def update_lambda_memory(function_name, memory_size):
    lambda_client = boto3.client('lambda')
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        MemorySize=int(memory_size)
    )

def lambda_handler(event, context):
    ssm_client = boto3.client('ssm')
    function_name = event['detail']['name'].split("/")[-1]
    response = ssm_client.get_parameter(Name=event['detail']['name'])
    memory_size = response['Parameter']['Value']
    
    update_lambda_memory(function_name, memory_size)
    return {'status': 'Updated Lambda memory'}