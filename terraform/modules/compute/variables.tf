variable "environment" {
  description = "Environment name"
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

variable "rds_address" {
  description = "RDS address"
  type        = string
}

variable "redis_address" {
  description = "Redis address"
  type        = string
}

variable "docdb_address" {
  description = "DocumentDB address"
  type        = string
}

variable "mysql_address" {
  description = "MySQL address"
  type        = string
}

variable "api_desired_count" {
  description = "Number of API replicas"
  type        = number
}

variable "worker_desired_count" {
  description = "Number of Worker replicas"
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
