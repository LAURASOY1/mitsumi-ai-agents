# /terraform/outputs.tf
# NETWORKING OUTPUTS
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = module.networking.database_subnet_ids
}

# SECURITY OUTPUTS
output "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  value       = module.security.ecs_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = module.security.ecs_task_role_arn
}

# DATABASE OUTPUTS
output "mongodb_address" {
  description = "MongoDB (DocumentDB) address"
  value       = module.databases.mongodb_address
}

output "mongodb_username" {
  description = "MongoDB username"
  value       = module.databases.mongodb_username
  sensitive   = true
}

output "mongodb_database" {
  description = "MongoDB database name"
  value       = module.databases.mongodb_database
}

output "mongodb_secret_arn" {
  description = "MongoDB secret ARN"
  value       = module.databases.mongodb_secret_arn
}

output "redis_address" {
  description = "Redis address"
  value       = module.databases.redis_address
}

output "redis_secret_arn" {
  description = "Redis secret ARN"
  value       = module.databases.redis_secret_arn
}

output "kms_key_id" {
  description = "KMS Key ID"
  value       = module.databases.kms_key_id
}

# COMPUTE OUTPUTS
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.compute.alb_dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = module.compute.alb_arn
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.compute.ecr_repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.compute.ecs_cluster_name
}

output "api_service_name" {
  description = "API service name"
  value       = module.compute.api_service_name
}

output "target_group_arn" {
  description = "Target group ARN"
  value       = module.compute.target_group_arn
}

output "api_log_group_name" {
  description = "API CloudWatch log group name"
  value       = "/ecs/mitsumi-api-${var.environment}"
}

# S3 OUTPUTS
output "backup_bucket_name" {
  description = "Backup bucket name"
  value       = aws_s3_bucket.backups.id
}

output "logs_bucket_name" {
  description = "ALB logs bucket name"
  value       = aws_s3_bucket.logs.id
}