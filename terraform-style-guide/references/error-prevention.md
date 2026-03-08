# Error Prevention & Recovery

## Table of Contents

- [Common Anti-Patterns](#common-anti-patterns)
- [Lifecycle Rules](#lifecycle-rules)
- [Dependency Management](#dependency-management)
- [State Management](#state-management)
- [Import Existing Resources](#import-existing-resources)
- [Recovery Commands](#recovery-commands)

## Common Anti-Patterns

### Do NOT

- Use `count` with a list that may reorder — use `for_each` with stable keys
- Reference `terraform.workspace` in resource names for environment isolation — use separate state files
- Hardcode provider credentials anywhere — use environment variables or IAM roles
- Run `terraform apply` without reviewing the plan
- Use `terraform taint` (deprecated) — use `terraform apply -replace=ADDR`
- Modify state manually — use `terraform state` subcommands

### Avoid

- Deeply nested modules (max 2-3 levels)
- Circular references between modules
- Using `depends_on` on modules unless absolutely necessary — it forces full recreation
- Storing large files or binary data in Terraform state via `local_file`

## Lifecycle Rules

Use `lifecycle` blocks to prevent accidental destruction and control update behavior:

```hcl
resource "aws_db_instance" "main" {
  # ...

  lifecycle {
    # Create replacement before destroying original (zero-downtime)
    create_before_destroy = true

    # Block accidental deletion of critical resources
    prevent_destroy = true

    # Ignore external changes to specific attributes
    ignore_changes = [tags, engine_version]
  }
}
```

### When to Use Each Rule

| Rule | Use When |
|------|----------|
| `create_before_destroy` | Zero-downtime required (load balancers, DNS records, DB instances) |
| `prevent_destroy` | Critical stateful resources (databases, encryption keys, S3 buckets with data) |
| `ignore_changes` | Attributes managed outside Terraform (auto-scaling tags, manually set fields) |

**Warning**: `prevent_destroy` blocks `terraform destroy` for the entire configuration. Only use on truly critical resources.

## Dependency Management

### Implicit Dependencies (Preferred)

Terraform automatically determines dependencies from attribute references:

```hcl
# Terraform knows the subnet depends on the VPC
resource "aws_subnet" "main" {
  vpc_id = aws_vpc.main.id  # implicit dependency
}
```

### Explicit Dependencies (Last Resort)

Use `depends_on` only when Terraform cannot infer the dependency:

```hcl
resource "aws_instance" "app" {
  ami           = "ami-abc123"
  instance_type = "t3.micro"

  # Required: IAM policy must exist before instance can assume role
  depends_on = [aws_iam_role_policy.app]
}
```

### Breaking Dependency Cycles

If `terraform plan` reports a cycle:

1. Identify the cycle from the error message
2. Extract the shared dependency into a separate resource
3. Use `depends_on` sparingly to break the cycle
4. Consider restructuring into separate modules

## State Management

### Remote Backend Configuration

Always use a remote backend for team projects:

```hcl
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "mycompanytfstate"
    container_name       = "tfstate"
    key                  = "project/environment.tfstate"
  }
}
```

### State Locking

- S3 backend: use DynamoDB table for locking
- Azure backend: locking built into blob lease
- GCS backend: locking built-in
- Never run concurrent applies against the same state

## Import Existing Resources

### Import Block (Terraform 1.5+, Preferred)

```hcl
import {
  to = aws_instance.web
  id = "i-0abc123def456789"
}

resource "aws_instance" "web" {
  ami           = "ami-abc123"
  instance_type = "t3.micro"
  # Write config to match existing resource
}
```

Run `terraform plan` to verify the import matches. Remove the `import` block after successful apply.

### Check Blocks (Terraform 1.5+)

Use `check` blocks for continuous validation of infrastructure health:

```hcl
check "api_health" {
  data "http" "api" {
    url = "https://${aws_lb.main.dns_name}/health"
  }

  assert {
    condition     = data.http.api.status_code == 200
    error_message = "API health check failed"
  }
}
```

## Recovery Commands

### Safe Apply Workflow

```bash
# Always plan first, save to file
terraform plan -out=tfplan

# Review the plan, then apply the saved plan
terraform apply tfplan
```

### State Recovery

```bash
# Back up current state
terraform state pull > state-backup.json

# Remove a resource from state (without destroying it)
terraform state rm 'aws_instance.web'

# Move a resource to a new address
terraform state mv 'aws_instance.old' 'aws_instance.new'

# Replace a misbehaving resource on next apply
terraform apply -replace='aws_instance.web'
```

### Force Unlock

```bash
# Only use when you are certain no other operation is running
terraform force-unlock LOCK_ID
```
