module "networking" {
  source = "./modules/networking"
  
  environment          = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones   = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
}
# MODULE: SECURITY

module "security" {
  source = "./modules/security"
  
  environment   = var.environment
  vpc_id        = module.networking.vpc_id
}

# MODULE: DATABASES
module "databases" {
  source = "./modules/databases"
  
  environment           = var.environment
  vpc_id               = module.networking.vpc_id
  database_subnet_ids  = module.networking.database_subnet_ids
  security_group_ids   = [module.security.database_sg_id]
  
  rds_instance_class    = var.rds_instance_class
  rds_allocated_storage = var.rds_allocated_storage
  rds_backup_retention  = var.rds_backup_retention_days
  
  redis_node_type       = var.redis_node_type
  docdb_instance_class  = var.docdb_instance_class
  mysql_instance_class  = var.mysql_instance_class
}

# MODULE: COMPUTE
module "compute" {
  source = "./modules/compute"
  
  environment   = var.environment
  vpc_id        = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  
  alb_sg_id     = module.security.alb_sg_id
  ecs_sg_id     = module.security.ecs_sg_id
  
  ecs_execution_role_arn = module.security.ecs_execution_role_arn
  ecs_task_role_arn      = module.security.ecs_task_role_arn
  
  rds_address   = module.databases.rds_address
  redis_address = module.databases.redis_address
  docdb_address = module.databases.docdb_address
  mysql_address = module.databases.mysql_address
  
  api_desired_count  = var.api_desired_count
  worker_desired_count = var.worker_desired_count
  api_cpu           = var.api_cpu
  api_memory        = var.api_memory
}
