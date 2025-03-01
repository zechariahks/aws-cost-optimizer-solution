import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Parse SSM parameter update event
        param_name = event['detail']['name']
        
        ssm_client = boto3.client('ssm')
        ec2_client = boto3.client('ec2')
        
        # Get parameter value
        param_response = ssm_client.get_parameter(Name=param_name)
        param_value = json.loads(param_response['Parameter']['Value'])
        
        instance_id = param_value['instance_id']
        recommended_type = param_value['recommended_type']
        
        # Get current instance configuration
        response = ec2_client.describe_instances(
            InstanceIds=[instance_id]
        )
        
        if not response['Reservations']:
            raise Exception(f"Instance {instance_id} not found")
            
        instance = response['Reservations'][0]['Instances'][0]
        
        # Check if instance is stopped
        if instance['State']['Name'] == 'stopped':
            # Modify instance type
            ec2_client.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceType={'Value': recommended_type}
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully updated instance {instance_id} to {recommended_type}',
                    'timestamp': datetime.now().isoformat()
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'Instance {instance_id} must be stopped first',
                    'current_state': instance['State']['Name'],
                    'timestamp': datetime.now().isoformat()
                })
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
