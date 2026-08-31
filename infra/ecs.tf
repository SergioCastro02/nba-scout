resource "aws_ecr_repository" "this" {
  name                 = local.name
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "this" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

locals {
  image = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"

  common_env = [
    { name = "NBA_SCOUT_VECTOR_STORE", value = "pgvector" },
    { name = "NBA_SCOUT_LLM_PROVIDER", value = var.llm_provider },
    { name = "NBA_SCOUT_BEDROCK_MODEL", value = var.bedrock_model },
    { name = "NBA_SCOUT_EMBEDDING_PROVIDER", value = var.embedding_provider },
    { name = "NBA_SCOUT_EMBEDDING_DIM", value = tostring(var.embedding_dim) },
    { name = "NBA_SCOUT_AWS_REGION", value = var.region },
  ]

  log_config = {
    logDriver = "awslogs"
    options = {
      "awslogs-group"         = aws_cloudwatch_log_group.this.name
      "awslogs-region"        = var.region
      "awslogs-stream-prefix" = "ecs"
    }
  }
}

# --------------------------------------------------------------------------- #
# API service                                                                  #
# --------------------------------------------------------------------------- #
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name             = "api"
      image            = local.image
      essential        = true
      command          = ["serve", "--host", "0.0.0.0", "--port", tostring(local.container_port)]
      portMappings     = [{ containerPort = local.container_port, protocol = "tcp" }]
      environment      = local.common_env
      secrets          = local.container_secrets
      logConfiguration = local.log_config
    }
  ])
}

resource "aws_lb" "this" {
  name               = local.name
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "api" {
  name        = local.name
  port        = local.container_port
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/healthz"
    matcher             = "200"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true # default VPC has no NAT; needed to pull the image
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = local.container_port
  }

  depends_on = [aws_lb_listener.http]
}

# --------------------------------------------------------------------------- #
# Ingestion task — run on demand: aws ecs run-task ... (see infra/README.md)    #
# --------------------------------------------------------------------------- #
resource "aws_ecs_task_definition" "ingest" {
  family                   = "${local.name}-ingest"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name             = "ingest"
      image            = local.image
      essential        = true
      command          = ["ingest", "-v"]
      environment      = local.common_env
      secrets          = local.container_secrets
      logConfiguration = local.log_config
    }
  ])
}
