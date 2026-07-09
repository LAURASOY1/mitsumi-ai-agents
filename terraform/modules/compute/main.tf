resource "aws_ecr_repository" "api" {
  name                 = "mitsumi-api-${var.environment}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name = "mitsumi-api-ecr-${var.environment}"
  }
}

# APPLICATION LOAD BALANCER
resource "aws_lb" "main" {
  name               = "mitsumi-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_sg_id]
  subnets            = var.public_subnet_ids
  
  tags = {
    Name = "mitsumi-alb-${var.environment}"
  }
}

# TARGET GROUP

resource "aws_lb_target_group" "api" {
  name        = "mitsumi-api-tg-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  stickiness {
    enabled         = true
    type            = "lb_cookie"
    cookie_duration = 3600  # ✅ FIXED: Changed from "duration" to "cookie_duration"
  }
  
  health_check {
    enabled             = true
    path               = "/health"
    interval           = 30
    timeout            = 5
    healthy_threshold  = 2
    unhealthy_threshold = 2
    matcher            = "200"
  }
  
  tags = {
    Name = "mitsumi-api-tg-${var.environment}"
  }
}

# HTTPS LISTENER
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  
  ssl_policy      = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn = "arn:aws:acm:eu-west-1:123456789012:certificate/example"  # REPLACE WITH YOUR ACM ARN
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# HTTP LISTENER (REDIRECT TO HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ECS CLUSTER

resource "aws_ecs_cluster" "main" {
  name = "mitsumi-cluster-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "mitsumi-cluster-${var.environment}"
  }
}

# ECS TASK DEFINITION - API

resource "aws_ecs_task_definition" "api" {
  family                   = "mitsumi-api-${var.environment}"
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = var.api_cpu
  memory                  = var.api_memory
  
  task_role_arn      = var.ecs_task_role_arn
  execution_role_arn = var.ecs_execution_role_arn
  
  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.api.repository_url}:latest"
      
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "LOG_LEVEL", value = "INFO" },
        { name = "DEBUG", value = "false" }
      ]
      
      secrets = [
        { name = "DATABASE_URL", valueFrom = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:prod/database" },
        { name = "REDIS_URL", valueFrom = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:prod/redis" }
      ]
      
      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 60
      }
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group" = "/ecs/mitsumi-api-${var.environment}"
          "awslogs-region" = "eu-west-1"
          "awslogs-stream-prefix" = "api"
        }
      }
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
    }
  ])
  
  tags = {
    Name = "mitsumi-api-td-${var.environment}"
  }
}

# ECS SERVICE - API
resource "aws_ecs_service" "api" {
  name            = "mitsumi-api-service-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }
  
  deployment_controller {
    type = "ECS"
  }
  
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  
  tags = {
    Name = "mitsumi-api-service-${var.environment}"
  }
}

# AUTO SCALING
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = var.api_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}


# CLOUDWATCH LOG GROUP

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/mitsumi-api-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Name = "mitsumi-api-logs-${var.environment}"
  }
}


# OUTPUTS

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}
