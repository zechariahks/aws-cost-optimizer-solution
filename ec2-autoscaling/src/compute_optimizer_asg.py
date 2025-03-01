import boto3
import json
import os
from datetime import datetime

def lambda_handler(event, context):
    try:
        client = boto3.client('compute-optimizer')
        ssm_client = boto3.client('ssm')
        autoscaling_client = boto3.client('autoscaling')
        
        # Get ASG recommendations
        response = client.get_auto_scaling_group_recommendations()
        
        recommendations_processed = 0
        for recommendation in response['autoScalingGroupRecommendations']:
            asg_name = recommendation['autoScalingGroupName']
            current_instance_type = recommendation['currentInstanceType']
            
            # Get ASG details
            asg_response = autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if asg_response['AutoScalingGroups']:
                # Get top recommendation
                if recommendation['recommendationOptions']:
                    recommended_instance_type = recommendation['recommendationOptions'][0]['instanceType']
                    
                    # Store recommendation in SSM
                    param_name = f"/asg/instance-type/{asg_name}"
                    param_value = json.dumps({
                        'asg_name': asg_name,
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
