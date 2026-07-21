#!/bin/bash

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "mitsumi-billing-alarm" \
  --alarm-description "Alert when monthly cost exceeds $2,000" \
  --metric-name "EstimatedCharges" \
  --namespace "AWS/Billing" \
  --statistic "Maximum" \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 2000 \
  --comparison-operator "GreaterThanThreshold" \
  --dimensions Name=Currency,Value=USD \
  --alarm-actions "arn:aws:sns:eu-west-1:${ACCOUNT_ID}:mitsumi-alerts"

echo "✅ Cost alarm created"
