# /terraform/modules/compute/variables.tf
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "ALB security group ID"
  type        = string
}

variable "ecs_sg_id" {
  description = "ECS security group ID"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "certificate_arn" {
  description = "ACM Certificate ARN"
  type        = string
}

variable "log_bucket_id" {
  description = "S3 bucket ID for ALB logs"
  type        = string
  default     = ""
}

variable "mongodb_secret_arn" {
  description = "MongoDB secret ARN"
  type        = string
}

variable "redis_secret_arn" {
  description = "Redis secret ARN"
  type        = string
}

variable "llm_secret_arn" {
  description = "LLM keys secret ARN"
  type        = string
}

variable "redis_address" {
  description = "Redis address"
  type        = string
}

variable "api_desired_count" {
  description = "Number of API replicas"
  type        = number
}

variable "api_cpu" {
  description = "API CPU units"
  type        = number
}

variable "api_memory" {
  description = "API memory in MB"
  type        = number
}