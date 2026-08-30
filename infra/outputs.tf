output "ecr_repository_url" {
  value = aws_ecr_repository.this.repository_url
}

output "api_url" {
  value = "http://${aws_lb.this.dns_name}"
}

output "health_url" {
  value = "http://${aws_lb.this.dns_name}/healthz"
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "ingest_task_family" {
  value = aws_ecs_task_definition.ingest.family
}

output "run_ingest_command" {
  description = "Populate the knowledge base after the first deploy"
  value = join(" ", [
    "aws ecs run-task",
    "--cluster ${aws_ecs_cluster.this.name}",
    "--task-definition ${aws_ecs_task_definition.ingest.family}",
    "--launch-type FARGATE",
    "--network-configuration 'awsvpcConfiguration={subnets=[${join(",", data.aws_subnets.default.ids)}],securityGroups=[${aws_security_group.service.id}],assignPublicIp=ENABLED}'",
  ])
}
