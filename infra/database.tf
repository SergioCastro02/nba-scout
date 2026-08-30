# RDS Postgres with the pgvector extension.
# `nba_scout` runs `CREATE EXTENSION IF NOT EXISTS vector` on first ingest; the
# master user has rights to create it (pgvector is on RDS's default allow-list).

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = local.name
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "this" {
  identifier     = local.name
  engine         = "postgres"
  engine_version = "16"

  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "nba_scout"
  username = "nba"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false

  multi_az                   = false
  backup_retention_period    = 7
  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true

  apply_immediately = true
}

locals {
  database_url = format(
    "postgresql://%s:%s@%s/%s",
    aws_db_instance.this.username,
    random_password.db.result,
    aws_db_instance.this.endpoint,
    aws_db_instance.this.db_name,
  )
}
