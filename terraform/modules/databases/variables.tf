variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "database_subnet_ids" {
  description = "Database subnet IDs"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs"
  type        = list(string)
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "rds_allocated_storage" {
  description = "RDS storage size"
  type        = number
}

variable "rds_backup_retention" {
  description = "RDS backup retention days"
  type        = number
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
}

variable "docdb_instance_class" {
  description = "DocumentDB instance class"
  type        = string
}

variable "mysql_instance_class" {
  description = "MySQL instance class"
  type        = string
}