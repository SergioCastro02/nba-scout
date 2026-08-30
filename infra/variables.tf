variable "region" {
  type    = string
  default = "us-east-1"
}

variable "image_tag" {
  description = "Container image tag to deploy (pushed to the ECR repo this stack creates)"
  type        = string
  default     = "latest"
}

# --- LLM / embeddings -------------------------------------------------------- #
variable "llm_provider" {
  description = "bedrock (uses the task IAM role) | anthropic | google (needs llm_api_key_secret_arn)"
  type        = string
  default     = "bedrock"
}

variable "bedrock_model" {
  type    = string
  default = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
}

variable "embedding_provider" {
  description = "bedrock | fastembed (local, in-image)"
  type        = string
  default     = "bedrock"
}

variable "embedding_dim" {
  description = "Must match the embedding model: 1024 for Titan v2, 384 for bge-small"
  type        = number
  default     = 1024
}

variable "llm_api_key_secret_arn" {
  description = "Secrets Manager ARN holding the Anthropic/Google API key (only for those providers)"
  type        = string
  default     = ""
}

# --- sizing --------------------------------------------------------------- #
variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "allowed_cidr" {
  description = "CIDR allowed to reach the load balancer"
  type        = string
  default     = "0.0.0.0/0"
}

variable "log_retention_days" {
  type    = number
  default = 14
}
