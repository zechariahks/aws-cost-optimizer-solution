# Optimize EC2 Instance Costs with AWS Compute Optimizer

## Description

This solution provides an automated method for optimizing AWS EC2 instance configurations using AWS Compute Optimizer recommendations. The recommendations are stored in AWS SSM Parameter Store, enabling seamless integration with Infrastructure-as-Code (IaC) deployments. An EventBridge Scheduler triggers a Lambda function periodically to fetch Compute Optimizer insights and update SSM parameters. Another EventBridge rule monitors parameter changes and triggers instance updates during maintenance windows.

---

## Implementation Steps

### Step 1: Enable AWS Compute Optimizer

#### Using AWS Console:
1. Navigate to the **AWS Compute Optimizer** console
2. Click on **Get Started** and choose **Opt In**
3. Ensure Compute Optimizer has sufficient time (at least 24 hours) to analyze EC2 metrics

#### Using AWS CLI:
```bash
aws compute-optimizer update-enrollment-status --status Active
```

### Step 2: Create IAM Roles

#### Using AWS Console:

1. Navigate to IAM Console
2. Create role for Compute Optimizer Lambda:
    - Choose Lambda as the service
    - Add these policies:
        - AWSLambdaBasicExecutionRole
        - Custom policy for Compute Optimizer access
        - Custom policy for SSM Parameter Store access
3. Create role for EC2 Update Lambda:
    - Choose Lambda as the service
    - Add these policies:
        - AWSLambdaBasicExecutionRole
        - Custom policy for EC2 actions
        - Custom policy for SSM Parameter Store access

Using AWS CLI:

```sh
# Create Compute Optimizer Lambda Role
aws iam create-role \
    --role-name ec2_compute_optimizer_role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach necessary policies
aws iam attach-role-policy \
    --role-name ec2_compute_optimizer_role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy \
    --role-name ec2_compute_optimizer_role \
    --policy-name ComputeOptimizerAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "compute-optimizer:GetEC2InstanceRecommendations",
                "ec2:DescribeInstances",
                "ssm:PutParameter"
            ],
            "Resource": "*"
        }]
    }'

# Create EC2 Update Lambda Role
aws iam create-role \
    --role-name ec2_update_role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach necessary policies
aws iam attach-role-policy \
    --role-name ec2_update_role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy \
    --role-name ec2_update_role \
    --policy-name UpdateEC2Config \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ec2:ModifyInstanceAttribute",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ssm:GetParameter"
            ],
            "Resource": "*"
        }]
    }'
```

### Step 3: Create Lambda Functions

#### Method 1: Using AWS Console

1. **Create Compute Optimizer Lambda:**
   - Go to AWS Lambda console
   - Click "Create function"
   - Choose "Author from scratch"
   - Enter function name: `compute_optimizer_ec2`
   - Runtime: Python 3.8
   - Select existing role: `ec2_compute_optimizer_role`
   - Click "Create function"
   - Copy code from `src/compute_optimizer_ec2.py`

2. **Create EC2 Update Lambda:**
   - Go to AWS Lambda console
   - Click "Create function"
   - Choose "Author from scratch"
   - Enter function name: `update_ec2_instance`
   - Runtime: Python 3.8
   - Select existing role: `ec2_update_role`
   - Click "Create function"
   - Copy code from `src/update_ec2_instance.py`

#### Method 2: Using AWS CLI

```bash
# Create deployment packages
cd src
zip -r ../compute_optimizer_ec2.zip compute_optimizer_ec2.py
zip -r ../update_ec2_instance.zip update_ec2_instance.py

# Deploy Lambda functions
aws lambda create-function \
    --function-name compute_optimizer_ec2 \
    --runtime python3.8 \
    --handler compute_optimizer_ec2.lambda_handler \
    --role $(aws iam get-role --role-name ec2_compute_optimizer_role --query 'Role.Arn' --output text) \
    --zip-file fileb://compute_optimizer_ec2.zip

aws lambda create-function \
    --function-name update_ec2_instance \
    --runtime python3.8 \
    --handler update_ec2_instance.lambda_handler \
    --role $(aws iam get-role --role-name ec2_update_role --query 'Role.Arn' --output text) \
    --zip-file fileb://update_ec2_instance.zip
```

### Step 4: Create EventBridge Rules

#### Method 1: Using AWS Console

1. **Create Scheduler Rule:**
    - Go to Amazon EventBridge console
    - Click "Create rule"
    - Enter rule name: "EC2OptimizationSchedule"
    - Select "Schedule pattern"
    - Enter schedule expression (e.g., rate(1 day))
    - Select target: Lambda function compute_optimizer_ec2
    - Click "Create"

2. **Create Parameter Change Rule:**
    - Go to Amazon EventBridge console
    - Click "Create rule"
    - Enter rule name: "EC2ParameterChangeRule"
    - Select "Event pattern"
    - Service: AWS services
    - Service name: Parameter Store
    - Event type: Parameter Store Change
    - Select specific parameter names: prefix "/ec2/instance-type/"
    - Select target: Lambda function update_ec2_instance
    - Click "Create"

#### Method 2: Using AWS CLI

```sh
# Create Scheduler Rule
aws events put-rule \
    --name EC2OptimizationSchedule \
    --schedule-expression "rate(1 day)"

aws events put-targets \
    --rule EC2OptimizationSchedule \
    --targets "Id"="1","Arn"="$(aws lambda get-function --function-name compute_optimizer_ec2 --query 'Configuration.FunctionArn' --output text)"

# Create Parameter Change Rule
aws events put-rule \
    --name EC2ParameterChangeRule \
    --event-pattern '{
        "source": ["aws.ssm"],
        "detail-type": ["Parameter Store Change"],
        "detail": {
            "name": [{
                "prefix": "/ec2/instance-type/"
            }],
            "operation": ["Update"]
        }
    }'

aws events put-targets \
    --rule EC2ParameterChangeRule \
    --targets "Id"="1","Arn"="$(aws lambda get-function --function-name update_ec2_instance --query 'Configuration.FunctionArn' --output text)"

# Add Lambda permissions
aws lambda add-permission \
    --function-name compute_optimizer_ec2 \
    --statement-id EventBridgeScheduleInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name EC2OptimizationSchedule --query 'Arn' --output text)

aws lambda add-permission \
    --function-name update_ec2_instance \
    --statement-id EventBridgeParameterInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name EC2ParameterChangeRule --query 'Arn' --output text)
```

### Step 5: Testing and Validation

1. **Test Compute Optimizer Lambda:**
    - Invoke the Lambda function manually:
    ```sh
    aws lambda invoke \
        --function-name compute_optimizer_ec2 \
        --payload '{}' \
        response.json
    ```
    - Check the response:
    ```sh
    cat response.json
    ```

2. **Test SSM Parameter Updates:**
    - Create a test parameter:
    ```sh
    aws ssm put-parameter \
        --name "/ec2/instance-type/test-instance" \
        --value '{"instance_id":"i-1234567890abcdef0","current_type":"t3.micro","recommended_type":"t3.small"}' \
        --type String \
        --overwrite
    ```

3. **Monitor CloudWatch Logs:**
    - Get log events:
    ```sh
    aws logs get-log-events \
        --log-group-name "/aws/lambda/compute_optimizer_ec2" \
        --log-stream-name $(aws logs describe-log-streams \
            --log-group-name "/aws/lambda/compute_optimizer_ec2" \
            --order-by LastEventTime \
            --descending \
            --limit 1 \
            --query 'logStreams[0].logStreamName' \
            --output text)
    ```

### Step 6: Clean Up

#### Method 1: Using CloudFormation

1. Delete the CloudFormation stack:
    ```sh
    aws cloudformation delete-stack --stack-name ec2-cost-optimization
    ```
2. Wait for stack deletion to complete:
    ```sh
    aws cloudformation wait stack-delete-complete --stack-name ec2-cost-optimization
    ```

#### Method 2: Manual Cleanup

1. **Delete EventBridge Rules:**
    ```sh
    aws events remove-targets --rule EC2OptimizationSchedule --ids "1"
    aws events delete-rule --name EC2OptimizationSchedule

    aws events remove-targets --rule EC2ParameterChangeRule --ids "1"
    aws events delete-rule --name EC2ParameterChangeRule
    ```

2. **Delete Lambda Functions:**
    ```sh
    aws lambda delete-function --function-name compute_optimizer_ec2
    aws lambda delete-function --function-name update_ec2_instance
    ```

3. **Delete IAM Roles and Policies:**
    ```sh
    aws iam delete-role-policy --role-name ec2_compute_optimizer_role --policy-name ComputeOptimizerAccess
    aws iam detach-role-policy --role-name ec2_compute_optimizer_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam delete-role --role-name ec2_compute_optimizer_role

    aws iam delete-role-policy --role-name ec2_update_role --policy-name UpdateEC2Config
    aws iam detach-role-policy --role-name ec2_update_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam delete-role --role-name ec2_update_role
    ```

4. **Clean up SSM Parameters:**
    ```sh
    aws ssm get-parameters-by-path --path "/ec2/instance-type/" --recursive | \
    jq -r '.Parameters[].Name' | \
    while read param; do
        aws ssm delete-parameter --name "$param"
    done
    ```