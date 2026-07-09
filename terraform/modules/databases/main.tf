resource "random_password" "rds" {
  length  = 32
  special = false
}

resource "random_password" "mysql" {
  length  = 32
  special = false
}

resource "random_password" "redis" {
  length  = 32
  special = false
}

resource "random_password" "docdb" {
  length  = 32
  special = false
}

# kms key for encrypting secrets
resource "aws_kms_key" "main" {
  description             = "Mitsumi encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name = "mitsumi-kms-${var.environment}"
  }
}

# SECRETS MANAGER - Database
resource "aws_secretsmanager_secret" "database" {
  name = "prod/database"
  description = "Database credentials"
  
  tags = {
    Name = "mitsumi-database-secret"
  }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = "mitsumi_admin"
    password = random_password.rds.result
    host     = aws_rds_cluster.main.endpoint
    port     = 5432
    database = "mitsumi_db"
  })
}

# SECRETS MANAGER - Redis
resource "aws_secretsmanager_secret" "redis" {
  name = "prod/redis"
  description = "Redis credentials"
  
  tags = {
    Name = "mitsumi-redis-secret"
  }
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host     = aws_elasticache_cluster.main.cache_nodes[0].address
    port     = 6379
    password = random_password.redis.result
  })
}

# DB SUBNET GROUP
resource "aws_db_subnet_group" "main" {
  name        = "mitsumi-db-subnet-${var.environment}"
  description = "Database subnet group"
  subnet_ids  = var.database_subnet_ids
  
  tags = {
    Name = "mitsumi-db-subnet-${var.environment}"
  }
}

# AURORA POSTGRESQL (with pgvector)
resource "aws_rds_cluster" "main" {
  cluster_identifier = "mitsumi-postgres-${var.environment}"
  engine             = "aurora-postgresql"
  engine_version     = "16.1"
  database_name      = "mitsumi_db"
  master_username    = "mitsumi_admin"
  master_password    = random_password.rds.result
  
  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.rds_backup_retention
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  storage_encrypted = true
  kms_key_id        = aws_kms_key.main.arn
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  serverlessv2_scaling_configuration {
    min_capacity = 2
    max_capacity = 16
  }
  
  tags = {
    Name = "mitsumi-postgres-${var.environment}"
  }
}

resource "aws_rds_cluster_instance" "main" {
  count = 2
  
  cluster_identifier = aws_rds_cluster.main.id
  identifier         = "mitsumi-postgres-${var.environment}-${count.index + 1}"
  instance_class     = var.rds_instance_class
  engine             = "aurora-postgresql"
  
  tags = {
    Name = "mitsumi-postgres-instance-${var.environment}-${count.index + 1}"
  }
}

# ELASTICACHE REDIS - Using aws_elasticache_cluster
resource "aws_elasticache_subnet_group" "redis" {
  name        = "mitsumi-redis-subnet-${var.environment}"
  description = "Redis subnet group"
  subnet_ids  = var.database_subnet_ids
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "mitsumi-redis-${var.environment}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = 2  # 1 primary + 1 replica
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = var.security_group_ids
  
  tags = {
    Name = "mitsumi-redis-${var.environment}"
  }
}

# DOCUMENTDB
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
  
  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = aws_docdb_subnet_group.main.name
  
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"
  
  storage_encrypted = true
  kms_key_id        = aws_kms_key.main.arn
  
  tags = {
    Name = "mitsumi-docdb-${var.environment}"
  }
}

resource "aws_docdb_cluster_instance" "main" {
  count = 2
  
  cluster_identifier = aws_docdb_cluster.main.id
  identifier         = "mitsumi-docdb-${var.environment}-${count.index + 1}"
  instance_class     = var.docdb_instance_class
  engine             = "docdb"
  
  tags = {
    Name = "mitsumi-docdb-instance-${var.environment}-${count.index + 1}"
  }
}


# RDS MYSQL
resource "aws_db_instance" "mysql" {
  identifier = "mitsumi-mysql-${var.environment}"
  
  engine         = "mysql"
  engine_version = "8.0.35"
  instance_class = var.mysql_instance_class
  
  allocated_storage   = 100
  max_allocated_storage = 200
  storage_encrypted   = true
  
  db_name  = "crm_db"
  username = "crm_user"
  password = random_password.mysql.result
  
  vpc_security_group_ids = var.security_group_ids
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window         = "03:00-04:00"
  maintenance_window    = "sun:04:00-sun:05:00"
  
  multi_az = true
  
  enabled_cloudwatch_logs_exports = ["general", "slowquery"]
  
  tags = {
    Name = "mitsumi-mysql-${var.environment}"
  }
}

# OUTPUTS
output "rds_address" {
  value = aws_rds_cluster.main.endpoint
}

output "redis_address" {
  value = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "docdb_address" {
  value = aws_docdb_cluster.main.endpoint
}

output "mysql_address" {
  value = aws_db_instance.mysql.address
}