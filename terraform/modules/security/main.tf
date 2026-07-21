# /terraform/modules/security/main.tf
# SECURITY GROUP - DATABASE (MongoDB Only)
resource "aws_security_group" "database" {
  name        = "mitsumi-database-sg-${var.environment}"
  description = "Database Security Group - MongoDB only"
  vpc_id      = var.vpc_id

  # MongoDB only - remove PostgreSQL, Redis, MySQL
  ingress {
    description     = "MongoDB from ECS"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  # Allow MongoDB replication traffic within the cluster
  ingress {
    description     = "MongoDB Replication"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    self            = true
  }

  # Allow MongoDB monitoring
  ingress {
    description     = "MongoDB Monitoring"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    cidr_blocks     = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mitsumi-database-sg-${var.environment}"
  }
}

# SECURITY GROUP - ECS
resource "aws_security_group" "ecs" {
  name        = "mitsumi-ecs-sg-${var.environment}"
  description = "ECS Security Group"
  vpc_id      = var.vpc_id

  ingress {
    description     = "API from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  # ECS to MongoDB
  egress {
    description     = "MongoDB"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.database.id]
  }

  # ECS to Redis (for caching/websockets)
  egress {
    description     = "Redis"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.redis_security_group_id]
  }

  # ECS to Internet (for LLM APIs, etc.)
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ECS to AWS Services (via VPC endpoints)
  egress {
    description     = "AWS Services"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    prefix_list_ids = [aws_vpc_endpoint.s3.prefix_list_id]
  }

  tags = {
    Name = "mitsumi-ecs-sg-${var.environment}"
  }
}

# SECURITY GROUP - REDIS (For Caching & WebSockets)
resource "aws_security_group" "redis" {
  name        = "mitsumi-redis-sg-${var.environment}"
  description = "Redis Security Group"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mitsumi-redis-sg-${var.environment}"
  }
}

# IAM ROLES
resource "aws_iam_role" "ecs_execution" {
  name = "mitsumi-ecs-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "mitsumi-ecs-execution-${var.environment}"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role with Secrets Manager Access
resource "aws_iam_role" "ecs_task" {
  name = "mitsumi-ecs-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "mitsumi-ecs-task-${var.environment}"
  }
}

# Secrets Manager Access Policy
resource "aws_iam_policy" "secrets" {
  name = "mitsumi-secrets-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${var.account_id}:secret:prod/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.secrets.arn
}

# CloudWatch Logs Access
resource "aws_iam_policy" "logs" {
  name = "mitsumi-logs-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/ecs/mitsumi-api-${var.environment}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.logs.arn
}

# SSM Parameter Store Access (for non-secret config)
resource "aws_iam_policy" "ssm" {
  name = "mitsumi-ssm-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${var.account_id}:parameter/mitsumi/${var.environment}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ssm.arn
}

# OUTPUTS
output "database_sg_id" {
  value = aws_security_group.database.id
}

output "ecs_sg_id" {
  value = aws_security_group.ecs.id
}

output "redis_sg_id" {
  value = aws_security_group.redis.id
}

output "ecs_execution_role_arn" {
  value = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  value = aws_iam_role.ecs_task.arn
}
