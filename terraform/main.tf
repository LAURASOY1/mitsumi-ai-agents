# /terraform/main.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  
  backend "s3" {
    bucket         = "mitsumi-terraform-state"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "mitsumi-ai"
      ManagedBy   = "terraform"
    }
  }
}

# ============================================
# MODULE: NETWORKING
# ============================================
module "networking" {
  source = "./modules/networking"

  environment          = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones   = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
}

# ============================================
# MODULE: SECURITY
# ============================================
module "security" {
  source = "./modules/security"

  environment   = var.environment
  aws_region    = var.aws_region
  account_id    = var.account_id
  vpc_id        = module.networking.vpc_id
  vpc_cidr      = var.vpc_cidr
  alb_security_group_id = module.networking.alb_security_group_id
}

# ============================================
# MODULE: DATABASES
# ============================================
module "databases" {
  source = "./modules/databases"

  environment   = var.environment
  vpc_id        = module.networking.vpc_id
  database_subnet_ids  = module.networking.database_subnet_ids
  
  mongodb_security_group_ids = [module.security.database_sg_id]
  redis_security_group_ids   = [module.security.redis_sg_id]

  docdb_instance_class  = var.docdb_instance_class
  redis_node_type       = var.redis_node_type
  
  openai_api_key     = var.openai_api_key
  anthropic_api_key  = var.anthropic_api_key
}

# ============================================
# MODULE: COMPUTE
# ============================================
module "compute" {
  source = "./modules/compute"

  environment   = var.environment
  aws_region    = var.aws_region
  vpc_id        = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids

  alb_sg_id     = module.networking.alb_security_group_id
  ecs_sg_id     = module.security.ecs_sg_id

  ecs_execution_role_arn = module.security.ecs_execution_role_arn
  ecs_task_role_arn      = module.security.ecs_task_role_arn

  certificate_arn = var.certificate_arn
  
  mongodb_secret_arn = module.databases.mongodb_secret_arn
  redis_secret_arn   = module.databases.redis_secret_arn
  llm_secret_arn     = module.databases.llm_secret_arn
  
  redis_address = module.databases.redis_address

  api_desired_count     = var.api_desired_count
  api_cpu               = var.api_cpu
  api_memory            = var.api_memory
}

# ============================================
# S3 BACKUP BUCKET
# ============================================
resource "aws_s3_bucket" "backups" {
  bucket = "mitsumi-backups-${var.environment}"
  force_destroy = false
  
  tags = {
    Name = "mitsumi-backups-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    id     = "archive-old-backups"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}

# S3 Bucket for ALB Logs
resource "aws_s3_bucket" "logs" {
  bucket = "mitsumi-alb-logs-${var.environment}"
  force_destroy = false
  
  tags = {
    Name = "mitsumi-alb-logs-${var.environment}"
  }
}

resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.logs.arn
      }
    ]
  })
}