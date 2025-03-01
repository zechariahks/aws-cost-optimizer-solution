import boto3
import json
import os
from datetime import datetime

def lambda_handler(event, context):
    try:
        client = boto3.client('compute-optimizer')
        ssm_client = boto3.client('ssm')
        rds_client = boto3.client('rds')
        
        # Get RDS instance recommendations
        response = client.get_rds_instance_recommendations()
        
        recommendations_processed = 0
        for recommendation in response['instanceRecommendations']:
            db_instance_id = recommendation['instanceArn'].split(':')[-1]
            current_instance_type = recommendation['currentInstanceType']
            
            # Get RDS instance details
            instance_response = rds_client.describe_db_instances(
                DBInstanceIdentifier=db_instance_id
            )
            
            if instance_response['DBInstances']:
                # Get top recommendation
                if recommendation['recommendationOptions']:
                    recommended_instance_type = recommendation['recommendationOptions'][0]['instanceType']
                    
                    # Store recommendation in SSM
                    param_name = f"/rds/instance-type/{db_instance_id}"
                    param_value = json.dumps({
                        'db_instance_id': db_instance_id,
                        'current_type': current_instance_type,
                        'recommended_type': recommended_instance_type,
                        'last_updated': datetime.now().isoformat()
                    })
                    
                    ssm_client.put_parameter(
                        Name=param_name,
                        Value=param_value,
                        Type='String',
                        Overwrite=True
                    )
                    
                    recommendations_processed += 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {recommendations_processed} recommendations',
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
