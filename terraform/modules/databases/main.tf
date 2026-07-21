# /terraform/modules/databases/main.tf
# RANDOM PASSWORDS
resource "random_password" "docdb" {
  length  = 32
  special = false
  min_upper = 8
  min_lower = 8
  min_numeric = 4
}

resource "random_password" "redis" {
  length  = 24
  special = false
}

# KMS KEY
resource "aws_kms_key" "main" {
  description             = "Mitsumi encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name = "mitsumi-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/mitsumi-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# ============================================
# SECRETS MANAGER
# ============================================

# MongoDB Secret
resource "aws_secretsmanager_secret" "mongodb" {
  name = "prod/mongodb"
  description = "MongoDB credentials"
  kms_key_id = aws_kms_key.main.arn
  
  tags = {
    Name = "mitsumi-mongodb-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "mongodb" {
  secret_id = aws_secretsmanager_secret.mongodb.id
  secret_string = jsonencode({
    username = "docdb_admin"
    password = random_password.docdb.result
    host     = aws_docdb_cluster.main.endpoint
    port     = 27017
    database = "mitsumi_agent"
    uri      = "mongodb://docdb_admin:${random_password.docdb.result}@${aws_docdb_cluster.main.endpoint}:27017/mitsumi_agent?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
  })
}

# Redis Secret
resource "aws_secretsmanager_secret" "redis" {
  name = "prod/redis"
  description = "Redis credentials"
  kms_key_id = aws_kms_key.main.arn
  
  tags = {
    Name = "mitsumi-redis-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host     = aws_elasticache_replication_group.main.primary_endpoint_address
    port     = 6379
    password = random_password.redis.result
    uri      = "redis://:${random_password.redis.result}@${aws_elasticache_replication_group.main.primary_endpoint_address}:6379/0"
  })
}

# LLM Keys Secret (for API keys)
resource "aws_secretsmanager_secret" "llm_keys" {
  name = "prod/llm-keys"
  description = "LLM API Keys"
  kms_key_id = aws_kms_key.main.arn
  
  tags = {
    Name = "mitsumi-llm-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "llm_keys" {
  secret_id = aws_secretsmanager_secret.llm_keys.id
  secret_string = jsonencode({
    openai     = var.openai_api_key
    anthropic  = var.anthropic_api_key
  })
}

# ============================================
# DOCUMENTDB (MongoDB Compatible)
# ============================================

resource "aws_docdb_subnet_group" "main" {
  name        = "mitsumi-docdb-subnet-${var.environment}"
  description = "DocumentDB subnet group"
  subnet_ids  = var.database_subnet_ids
}

resource "aws_docdb_cluster" "main" {
  cluster_identifier = "mitsumi-docdb-${var.environment}"
  engine             = "docdb"
  engine_version     = "5.0.0"
  master_username    = "docdb_admin"
  master_password    = random_password.docdb.result
  
  vpc_security_group_ids = var.mongodb_security_group_ids
  db_subnet_group_name   = aws_docdb_subnet_group.main.name
  
  backup_retention_period = var.environment == "prod" ? 30 : 7
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  storage_encrypted = true
  kms_key_id        = aws_kms_key.main.arn
  
  # Enable deletion protection in production
  deletion_protection = var.environment == "prod"
  
  # Skip final snapshot in dev/staging
  final_snapshot_identifier = var.environment == "prod" ? "mitsumi-docdb-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Enable CloudWatch logs
  enabled_cloudwatch_logs_exports = ["audit", "profiler"]
  
  # Enable TLS
  apply_immediately = var.environment != "prod"
  
  tags = {
    Name = "mitsumi-docdb-${var.environment}"
  }
}

resource "aws_docdb_cluster_instance" "main" {
  count = var.environment == "prod" ? 3 : 1
  
  cluster_identifier = aws_docdb_cluster.main.id
  identifier         = "mitsumi-docdb-${var.environment}-${count.index + 1}"
  instance_class     = var.docdb_instance_class
  engine             = "docdb"
  
  tags = {
    Name = "mitsumi-docdb-instance-${var.environment}-${count.index + 1}"
  }
}

# ============================================
# ELASTICACHE REDIS (For Caching & WebSockets)
# ============================================

resource "aws_elasticache_subnet_group" "main" {
  name        = "mitsumi-redis-subnet-${var.environment}"
  description = "Redis subnet group"
  subnet_ids  = var.database_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "mitsumi-redis-${var.environment}"
  description          = "Redis replication group for Mitsumi AI Platform"
  node_type            = var.redis_node_type
  port                 = 6379
  parameter_group_name = "default.redis7"
  
  engine         = "redis"
  engine_version = "7.1"
  
  # Use cluster mode disabled for simplicity
  num_node_groups = 1
  replicas_per_node_group = var.environment == "prod" ? 2 : 1
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = var.redis_security_group_ids
  
  # Enable backup
  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  snapshot_window         = "02:00-03:00"
  
  # Enable automatic failover in production
  automatic_failover_enabled = var.environment == "prod"
  
  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token = random_password.redis.result
  
  tags = {
    Name = "mitsumi-redis-${var.environment}"
  }
}

# ============================================
# OUTPUTS
# ============================================

output "mongodb_address" {
  value = aws_docdb_cluster.main.endpoint
}

output "mongodb_username" {
  value = "docdb_admin"
  sensitive = true
}

output "mongodb_database" {
  value = "mitsumi_agent"
}

output "mongodb_secret_arn" {
  value = aws_secretsmanager_secret.mongodb.arn
}

output "redis_address" {
  value = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_secret_arn" {
  value = aws_secretsmanager_secret.redis.arn
}

output "llm_secret_arn" {
  value = aws_secretsmanager_secret.llm_keys.arn
}

output "kms_key_id" {
  value = aws_kms_key.main.key_id
}

output "mongodb_security_group_id" {
  value = var.mongodb_security_group_ids[0]
}

output "redis_security_group_id" {
  value = var.redis_security_group_ids[0]
}