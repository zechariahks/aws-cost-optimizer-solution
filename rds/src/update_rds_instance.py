import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Parse SSM parameter update event
        param_name = event['detail']['name']
        
        ssm_client = boto3.client('ssm')
        rds_client = boto3.client('rds')
        
        # Get parameter value
        param_response = ssm_client.get_parameter(Name=param_name)
        param_value = json.loads(param_response['Parameter']['Value'])
        
        db_instance_id = param_value['db_instance_id']
        recommended_type = param_value['recommended_type']
        
        # Get current RDS instance configuration
        instance_response = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_id
        )
        
        if not instance_response['DBInstances']:
            raise Exception(f"DB Instance {db_instance_id} not found")
            
        db_instance = instance_response['DBInstances'][0]
        
        # Check if instance is available for modification
        if db_instance['DBInstanceStatus'] == 'available':
            # Modify RDS instance
            response = rds_client.modify_db_instance(
                DBInstanceIdentifier=db_instance_id,
                DBInstanceClass=recommended_type,
                ApplyImmediately=False  # Schedule change for next maintenance window
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully scheduled update for DB instance {db_instance_id} to {recommended_type}',
                    'timestamp': datetime.now().isoformat()
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': f'DB Instance {db_instance_id} is not available for modification',
                    'current_status': db_instance['DBInstanceStatus'],
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
