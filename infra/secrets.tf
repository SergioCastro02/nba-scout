# The database URL (with password) is stored in Secrets Manager and injected into
# the task definition as a `secrets` entry, never as plain-text env.

resource "aws_secretsmanager_secret" "database_url" {
  name = "${local.name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = local.database_url
}

locals {
  # Extra `secrets` block entries for the container (empty unless an LLM key secret is given).
  llm_secret_entries = var.llm_api_key_secret_arn == "" ? [] : [
    {
      name      = var.llm_provider == "anthropic" ? "NBA_SCOUT_ANTHROPIC_API_KEY" : "NBA_SCOUT_GOOGLE_API_KEY"
      valueFrom = var.llm_api_key_secret_arn
    }
  ]

  container_secrets = concat(
    [{ name = "NBA_SCOUT_DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn }],
    local.llm_secret_entries,
  )

  secret_arns = concat(
    [aws_secretsmanager_secret.database_url.arn],
    var.llm_api_key_secret_arn == "" ? [] : [var.llm_api_key_secret_arn],
  )
}
