# ENVIRONMENT VARIABLE
variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

# NETWORKING VARIABLES
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnet_cidrs" {
  description = "Database subnet CIDRs"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}


# DATABASE VARIABLES
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_allocated_storage" {
  description = "RDS storage size in GB"
  type        = number
  default     = 100
}

variable "rds_backup_retention_days" {
  description = "RDS backup retention days"
  type        = number
  default     = 30
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "docdb_instance_class" {
  description = "DocumentDB instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "mysql_instance_class" {
  description = "MySQL instance class"
  type        = string
  default     = "db.r6g.large"
}

# COMPUTE VARIABLES
variable "api_desired_count" {
  description = "Number of API replicas"
  type        = number
  default     = 3
}

variable "worker_desired_count" {
  description = "Number of Worker replicas"
  type        = number
  default     = 2
}

variable "api_cpu" {
  description = "API CPU units (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "api_memory" {
  description = "API memory in MB"
  type        = number
  default     = 2048
}
