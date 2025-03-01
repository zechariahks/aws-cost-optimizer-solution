# Optimize AWS RDS Costs with Automated Compute Optimizer Insights

## Description

This solution provides an automated and scalable method for optimizing AWS RDS instance configurations to enhance cost efficiency and performance. By leveraging AWS Compute Optimizer, instance recommendations for RDS instances are dynamically stored in AWS SSM Parameter Store, allowing for seamless integration with Infrastructure-as-Code (IaC) deployments. An EventBridge Scheduler triggers a Lambda function periodically, fetching Compute Optimizer insights, analyzing them, and updating the corresponding SSM parameters. Additionally, an EventBridge rule listens for SSM Parameter Store updates and triggers a Lambda function to adjust the RDS instance configurations dynamically.

---

## Introduction

Amazon RDS instance costs can significantly impact your AWS bill. Selecting the right instance type and size for your RDS instances is crucial for cost optimization. AWS Compute Optimizer uses machine learning to analyze instance metrics and provide recommendations for optimal instance types. This solution automates the process of implementing these recommendations while ensuring minimal disruption to your database workloads.

---

## Architecture Overview

### Components Used:

1. **AWS Compute Optimizer** – Provides instance type recommendations for RDS instances
2. **AWS SSM Parameter Store** – Stores optimal instance type configurations
3. **AWS Lambda (for automation)** – Fetches recommendations and updates parameters
4. **Amazon EventBridge Scheduler** – Triggers the optimization workflow periodically
5. **Amazon EventBridge Rule** – Listens for SSM parameter updates and triggers RDS updates
6. **AWS CloudFormation/Terraform** – Dynamically references SSM parameters during deployment
7. **Amazon RDS** – Manages database instance modifications

## Implementation Steps

### Step 1: Enable AWS Compute Optimizer

#### Using AWS Console:
1. Navigate to the **AWS Compute Optimizer** console
2. Click on **Get Started** and choose **Opt In**
3. Ensure Compute Optimizer has sufficient time (at least 24 hours) to analyze RDS metrics

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
3. Create role for RDS Update Lambda:
    - Choose Lambda as the service
    - Add these policies:
        - AWSLambdaBasicExecutionRole
        - Custom policy for RDS actions
        - Custom policy for SSM Parameter Store access

Using AWS CLI:

```sh
# Create Compute Optimizer Lambda Role
aws iam create-role \
    --role-name rds_compute_optimizer_role \
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
    --role-name rds_compute_optimizer_role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy \
    --role-name rds_compute_optimizer_role \
    --policy-name ComputeOptimizerAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "compute-optimizer:GetRDSInstanceRecommendations",
                "rds:DescribeDBInstances",
                "ssm:PutParameter"
            ],
            "Resource": "*"
        }]
    }'

# Create RDS Update Lambda Role
aws iam create-role \
    --role-name rds_update_role \
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
    --role-name rds_update_role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy \
    --role-name rds_update_role \
    --policy-name UpdateRDSConfig \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "rds:ModifyDBInstance",
                "rds:DescribeDBInstances",
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
   - Enter function name: `compute_optimizer_rds`
   - Runtime: Python 3.8
   - Select existing role: `rds_compute_optimizer_role`
   - Click "Create function"
   - Copy code from `src/compute_optimizer_rds.py`

2. **Create RDS Update Lambda:**
   - Go to AWS Lambda console
   - Click "Create function"
   - Choose "Author from scratch"
   - Enter function name: `update_rds_instance`
   - Runtime: Python 3.8
   - Select existing role: `rds_update_role`
   - Click "Create function"
   - Copy code from `src/update_rds_instance.py`

#### Method 2: Using AWS CLI

```bash
# Create deployment packages
cd src
zip -r ../compute_optimizer_rds.zip compute_optimizer_rds.py
zip -r ../update_rds_instance.zip update_rds_instance.py

# Deploy Lambda functions
aws lambda create-function \
    --function-name compute_optimizer_rds \
    --runtime python3.8 \
    --handler compute_optimizer_rds.lambda_handler \
    --role $(aws iam get-role --role-name rds_compute_optimizer_role --query 'Role.Arn' --output text) \
    --zip-file fileb://compute_optimizer_rds.zip

aws lambda create-function \
    --function-name update_rds_instance \
    --runtime python3.8 \
    --handler update_rds_instance.lambda_handler \
    --role $(aws iam get-role --role-name rds_update_role --query 'Role.Arn' --output text) \
    --zip-file fileb://update_rds_instance.zip
```

### Step 4: Create EventBridge Rules

#### Method 1: Using AWS Console

1. **Create Scheduler Rule:**
    - Go to Amazon EventBridge console
    - Click "Create rule"
    - Enter rule name: "RDSOptimizationSchedule"
    - Select "Schedule pattern"
    - Enter schedule expression (e.g., rate(1 day))
    - Select target: Lambda function compute_optimizer_rds
    - Click "Create"

2. **Create Parameter Change Rule:**
    - Go to Amazon EventBridge console
    - Click "Create rule"
    - Enter rule name: "RDSParameterChangeRule"
    - Select "Event pattern"
    - Service: AWS services
    - Service name: Parameter Store
    - Event type: Parameter Store Change
    - Select specific parameter names: prefix "/rds/instance-type/"
    - Select target: Lambda function update_rds_instance
    - Click "Create"

#### Method 2: Using AWS CLI

```sh
# Create Scheduler Rule
aws events put-rule \
    --name RDSOptimizationSchedule \
    --schedule-expression "rate(1 day)"

aws events put-targets \
    --rule RDSOptimizationSchedule \
    --targets "Id"="1","Arn"="$(aws lambda get-function --function-name compute_optimizer_rds --query 'Configuration.FunctionArn' --output text)"

# Create Parameter Change Rule
aws events put-rule \
    --name RDSParameterChangeRule \
    --event-pattern '{
        "source": ["aws.ssm"],
        "detail-type": ["Parameter Store Change"],
        "detail": {
            "name": [{
                "prefix": "/rds/instance-type/"
            }],
            "operation": ["Update"]
        }
    }'

aws events put-targets \
    --rule RDSParameterChangeRule \
    --targets "Id"="1","Arn"="$(aws lambda get-function --function-name update_rds_instance --query 'Configuration.FunctionArn' --output text)"

# Add Lambda permissions
aws lambda add-permission \
    --function-name compute_optimizer_rds \
    --statement-id EventBridgeScheduleInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name RDSOptimizationSchedule --query 'Arn' --output text)

aws lambda add-permission \
    --function-name update_rds_instance \
    --statement-id EventBridgeParameterInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name RDSParameterChangeRule --query 'Arn' --output text)
```

### Step 5: Testing and Validation

1. **Test Compute Optimizer Lambda:**
    - Invoke the Lambda function manually:
    ```sh
    aws lambda invoke \
        --function-name compute_optimizer_rds \
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
        --name "/rds/instance-type/test-db" \
        --value '{"db_instance_id":"test-db","current_type":"db.t3.micro","recommended_type":"db.t3.small"}' \
        --type String \
        --overwrite
    ```

3. **Monitor CloudWatch Logs:**
    - Get log events:
    ```sh
    aws logs get-log-events \
        --log-group-name "/aws/lambda/compute_optimizer_rds" \
        --log-stream-name $(aws logs describe-log-streams \
            --log-group-name "/aws/lambda/compute_optimizer_rds" \
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
    aws cloudformation delete-stack --stack-name rds-cost-optimization
    ```
2. Wait for stack deletion to complete:
    ```sh
    aws cloudformation wait stack-delete-complete --stack-name rds-cost-optimization
    ```

#### Method 2: Manual Cleanup

1. **Delete EventBridge Rules:**
    ```sh
    aws events remove-targets --rule RDSOptimizationSchedule --ids "1"
    aws events delete-rule --name RDSOptimizationSchedule

    aws events remove-targets --rule RDSParameterChangeRule --ids "1"
    aws events delete-rule --name RDSParameterChangeRule
    ```

2. **Delete Lambda Functions:**
    ```sh
    aws lambda delete-function --function-name compute_optimizer_rds
    aws lambda delete-function --function-name update_rds_instance
    ```

3. **Delete IAM Roles and Policies:**
    ```sh
    aws iam delete-role-policy --role-name rds_compute_optimizer_role --policy-name ComputeOptimizerAccess
    aws iam detach-role-policy --role-name rds_compute_optimizer_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam delete-role --role-name rds_compute_optimizer_role

    aws iam delete-role-policy --role-name rds_update_role --policy-name UpdateRDSConfig
    aws iam detach-role-policy --role-name rds_update_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    aws iam delete-role --role-name rds_update_role
    ```

4. **Clean up SSM Parameters:**
    ```sh
    aws ssm get-parameters-by-path --path "/rds/instance-type/" --recursive | \
    jq -r '.Parameters[].Name' | \
    while read param; do
        aws ssm delete-parameter --name "$param"
    done
    ```

### Best Practices

1. **Implementation Best Practices:**
    - Test in non-production environments first
    - Implement gradual rollout strategy
    - Set up proper monitoring and alerting
    - Document all changes and configurations
    - Use tags for better resource management

2. **Security Best Practices:**
    - Follow principle of least privilege for IAM roles
    - Encrypt sensitive data in SSM Parameter Store
    - Implement proper error handling
    - Use AWS Secrets Manager for sensitive credentials
    - Regular security audits

3. **Operational Best Practices:**
    - Regular backup of RDS configurations
    - Implement proper logging and monitoring
    - Set up alerts for failed operations
    - Maintain change management documentation
    - Regular testing of rollback procedures

4. **Cost Optimization Best Practices:**
    - Monitor cost savings after implementation
    - Regular review of Compute Optimizer recommendations
    - Set up cost allocation tags
    - Implement budget alerts
    - Regular cleanup of unused resources

5. **Database-Specific Best Practices:**
    - Schedule instance modifications during maintenance windows
    - Monitor performance metrics before and after changes
    - Maintain proper backup strategy
    - Consider read replicas for high-availability
    - Regular performance optimization