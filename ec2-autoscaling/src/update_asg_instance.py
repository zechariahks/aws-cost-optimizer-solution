import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Parse SSM parameter update event
        param_name = event['detail']['name']
        
        ssm_client = boto3.client('ssm')
        autoscaling_client = boto3.client('autoscaling')
        
        # Get parameter value
        param_response = ssm_client.get_parameter(Name=param_name)
        param_value = json.loads(param_response['Parameter']['Value'])
        
        asg_name = param_value['asg_name']
        recommended_type = param_value['recommended_type']
        
        # Get current ASG configuration
        asg_response = autoscaling_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        
        if not asg_response['AutoScalingGroups']:
            raise Exception(f"ASG {asg_name} not found")
            
        asg = asg_response['AutoScalingGroups'][0]
        
        # Update ASG launch template/configuration
        if 'LaunchTemplate' in asg:
            # Handle Launch Template update
            ec2_client = boto3.client('ec2')
            launch_template_id = asg['LaunchTemplate']['LaunchTemplateId']
            
            # Create new version of launch template
            response = ec2_client.create_launch_template_version(
                LaunchTemplateId=launch_template_id,
                SourceVersion=str(asg['LaunchTemplate']['Version']),
                LaunchTemplateData={
                    'InstanceType': recommended_type
                }
            )
            
            new_version = response['LaunchTemplateVersion']['VersionNumber']
            
            # Update ASG to use new version
            autoscaling_client.update_auto_scaling_group(
                AutoScalingGroupName=asg_name,
                LaunchTemplate={
                    'LaunchTemplateId': launch_template_id,
                    'Version': str(new_version)
                }
            )
        else:
            # Handle Launch Configuration update
            launch_config_name = f"{asg_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Get current launch configuration
            launch_config_response = autoscaling_client.describe_launch_configurations(
                LaunchConfigurationNames=[asg['LaunchConfigurationName']]
            )
            
            if launch_config_response['LaunchConfigurations']:
                current_config = launch_config_response['LaunchConfigurations'][0]
                
                # Create new launch configuration
                autoscaling_client.create_launch_configuration(
                    LaunchConfigurationName=launch_config_name,
                    ImageId=current_config['ImageId'],
                    InstanceType=recommended_type,
                    SecurityGroups=current_config['SecurityGroups'],
                    KeyName=current_config.get('KeyName'),
                    UserData=current_config.get('UserData'),
                    IamInstanceProfile=current_config.get('IamInstanceProfile')
                )
                
                # Update ASG with new launch configuration
                autoscaling_client.update_auto_scaling_group(
                    AutoScalingGroupName=asg_name,
                    LaunchConfigurationName=launch_config_name
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully updated ASG {asg_name} to use instance type {recommended_type}',
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
