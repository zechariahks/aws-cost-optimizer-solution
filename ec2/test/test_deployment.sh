#!/bin/bash

# Set variables
STACK_NAME="ec2-cost-optimizer"
REGION=$(aws configure get region)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting EC2 Cost Optimizer deployment test...${NC}"

# Test 1: Check if Compute Optimizer is enabled
echo -e "\n${YELLOW}Test 1: Checking Compute Optimizer status...${NC}"
OPTIMIZER_STATUS=$(aws compute-optimizer get-enrollment-status --query 'status' --output text)
if [ "$OPTIMIZER_STATUS" == "Active" ]; then
    echo -e "${GREEN}✓ Compute Optimizer is enabled${NC}"
else
    echo -e "${RED}✗ Compute Optimizer is not enabled${NC}"
    echo "Enabling Compute Optimizer..."
    aws compute-optimizer update-enrollment-status --status Active
fi

# Test 2: Deploy CloudFormation stack
echo -e "\n${YELLOW}Test 2: Deploying CloudFormation stack...${NC}"
aws cloudformation deploy \
    --template-file ../templates/ec2-optimizer-template.yml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_NAMED_IAM

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deployed successfully${NC}"
else
    echo -e "${RED}✗ Stack deployment failed${NC}"
    exit 1
fi

# Test 3: Check Lambda functions
echo -e "\n${YELLOW}Test 3: Testing Lambda functions...${NC}"

# Test Compute Optimizer Lambda
echo "Testing Compute Optimizer Lambda..."
aws lambda invoke \
    --function-name "${STACK_NAME}-optimizer" \
    --payload '{}' \
    response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Compute Optimizer Lambda test successful${NC}"
else
    echo -e "${RED}✗ Compute Optimizer Lambda test failed${NC}"
fi

# Test 4: Check SSM Parameters
echo -e "\n${YELLOW}Test 4: Testing SSM Parameter creation...${NC}"
aws ssm put-parameter \
    --name "/ec2/instance-type/test-instance" \
    --value '{"instance_id":"i-test","current_type":"t3.micro","recommended_type":"t3.small"}' \
    --type String \
    --overwrite

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSM Parameter creation successful${NC}"
else
    echo -e "${RED}✗ SSM Parameter creation failed${NC}"
fi

# Test 5: Check EventBridge Rules
echo -e "\n${YELLOW}Test 5: Checking EventBridge Rules...${NC}"
SCHEDULE_RULE=$(aws events describe-rule --name "${STACK_NAME}-schedule" --query 'State' --output text)
PARAMETER_RULE=$(aws events describe-rule --name "${STACK_NAME}-parameter" --query 'State' --output text)

if [ "$SCHEDULE_RULE" == "ENABLED" ] && [ "$PARAMETER_RULE" == "ENABLED" ]; then
    echo -e "${GREEN}✓ EventBridge Rules are enabled${NC}"
else
    echo -e "${RED}✗ EventBridge Rules check failed${NC}"
fi

echo -e "\n${YELLOW}Test Summary:${NC}"
echo "1. Compute Optimizer Status: $OPTIMIZER_STATUS"
echo "2. CloudFormation Stack: COMPLETE"
echo "3. Lambda Functions: TESTED"
echo "4. SSM Parameters: TESTED"
echo "5. EventBridge Rules: $SCHEDULE_RULE"

echo -e "\n${GREEN}Testing complete!${NC}"
