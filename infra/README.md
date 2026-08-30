# Deploy — AWS ECS Fargate + RDS

Terraform stack that runs `nba-scout` as a Fargate service behind an ALB, with the
knowledge base in RDS Postgres (pgvector) and the LLM on Bedrock.

```
Internet ─HTTP:80─► ALB ─(/healthz)─► ECS Fargate: nba-scout serve
                                          │
                     ┌────────────────────┼───────────────────┐
                     ▼                    ▼                   ▼
              RDS Postgres         AWS Bedrock         CloudWatch Logs
              (pgvector)      (InvokeModel via IAM)   + Container Insights

  one-shot ECS task: nba-scout ingest  → writes chunks to RDS
```

## What it creates

| Resource | Notes |
|---|---|
| ECR repository | `nba-scout` |
| RDS Postgres 16 | `db.t4g.micro`, encrypted, private, pgvector; password in Secrets Manager |
| ECS cluster + API service + task def | Fargate, Container Insights |
| ECS ingest task def | run on demand to (re)build the knowledge base |
| ALB + target group + listener | health check on `/healthz` |
| 3 security groups | ALB ← internet; tasks ← ALB; RDS ← tasks only |
| IAM execution role | managed policy + `secretsmanager:GetSecretValue` on this stack's secrets |
| IAM task role | `bedrock:InvokeModel` only (added only when a Bedrock provider is used) |
| Secrets Manager | database URL; optional Anthropic/Google key |
| CloudWatch log group | `/ecs/nba-scout` |

Defaults to **Bedrock** for both the LLM and embeddings, so the task role — not a
stored key — is the only credential. Set `llm_provider = "anthropic"` (or
`"google"`) plus `llm_api_key_secret_arn` to use those instead.

Uses the **default VPC** to keep the demo cheap. For production, move the tasks and
RDS into private subnets behind a NAT gateway.

## Deploy

```bash
cd infra
terraform init
terraform apply                       # creates ECR + everything else

ECR=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "${ECR%/*}"
docker build -t "$ECR:latest" ..
docker push "$ECR:latest"

aws ecs update-service --cluster nba-scout --service nba-scout-api --force-new-deployment

# populate the knowledge base (prints the exact command with your subnets/SG):
terraform output -raw run_ingest_command | bash
```

Then:

```bash
curl "$(terraform output -raw health_url)"
curl -N -X POST "$(terraform output -raw api_url)/ask/stream" \
  -H 'content-type: application/json' -d '{"question":"what is the second apron?"}'
```

## Bedrock model access

Enable access to the Claude model in the Bedrock console (Model access) in the
same region before deploying, or `InvokeModel` returns `AccessDeniedException`.

## Cost

RDS `db.t4g.micro` + 1 Fargate task + 1 ALB ≈ ~US$30–40/month. `terraform destroy`
when done.

## CI/CD

`.github/workflows/ci.yml` builds the image and runs `terraform validate` on every
PR. For continuous deploy, add an OIDC role and a job that runs the build/push/
update-service steps above.
