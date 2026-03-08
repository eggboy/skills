---
name: terraform-style-guide
description: Generate Terraform HCL code following HashiCorp's official style conventions and best practices. Use when writing, reviewing, or generating Terraform configurations, HCL code, infrastructure as code, Terraform modules, or refactoring existing Terraform projects. Not for Pulumi, CloudFormation, Bicep, or other IaC tools.
---

# Terraform Style Guide

Generate and maintain Terraform code following HashiCorp's official style conventions.

**Reference:** [HashiCorp Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)

**Supplementary references** (load as needed):

- **Modules**: See [references/modules.md](references/modules.md) for module structure, versioning, `moved` blocks, and reusable module design
- **Dynamic resources**: See [references/dynamic-resources.md](references/dynamic-resources.md) for decision guide on `for_each` vs `count` vs `dynamic` blocks
- **Error prevention**: See [references/error-prevention.md](references/error-prevention.md) for anti-patterns, lifecycle rules, state backends, import blocks, and recovery commands

## Code Generation Strategy

When generating Terraform code:

1. Start with provider configuration and version constraints
2. Create data sources before dependent resources
3. Build resources in dependency order
4. Add outputs for key resource attributes
5. Use variables for all configurable values

## File Organization

| File | Purpose |
|------|---------|
| `terraform.tf` | Terraform and provider version requirements |
| `providers.tf` | Provider configurations |
| `main.tf` | Primary resources and data sources |
| `variables.tf` | Input variable declarations (alphabetical) |
| `outputs.tf` | Output value declarations (alphabetical) |
| `locals.tf` | Local value declarations |

For modules, add `README.md` and follow the structure in [references/modules.md](references/modules.md).

## Code Formatting

Align equals signs for consecutive arguments. Place meta-arguments first, then arguments, then nested blocks, with `lifecycle` last:

```hcl
resource "aws_instance" "example" {
  # Meta-arguments first
  count = 3

  # Arguments (aligned =)
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # Nested blocks
  root_block_device {
    volume_size = 20
  }

  # Lifecycle last
  lifecycle {
    create_before_destroy = true
  }
}
```

## Naming Conventions

- **Lowercase with underscores** for all names
- **Descriptive nouns** excluding the resource type
- **Singular**, not plural
- Default to `main` when only one instance exists and a specific name adds no clarity

```hcl
# Bad
resource "aws_instance" "webAPI-aws-instance" {}
resource "aws_instance" "web_apis" {}
variable "name" {}

# Good
resource "aws_instance" "web_api" {}
resource "aws_vpc" "main" {}
variable "application_name" {}
```

## Variables and Outputs

Every variable requires `type` and `description`. Every output requires `description`. Mark secrets with `sensitive = true`:

```hcl
variable "instance_type" {
  description = "EC2 instance type for the web server"
  type        = string
  default     = "t2.micro"

  validation {
    condition     = contains(["t2.micro", "t2.small", "t2.medium"], var.instance_type)
    error_message = "Instance type must be t2.micro, t2.small, or t2.medium."
  }
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}
```

## Dynamic Resource Creation

Prefer `for_each` over `count` for multiple named resources. Use `count` only for conditional creation (0 or 1). For the full decision guide and `dynamic` block patterns, see [references/dynamic-resources.md](references/dynamic-resources.md).

```hcl
# for_each — stable keys, safe to add/remove
resource "aws_instance" "web" {
  for_each      = toset(["web-1", "web-2", "web-3"])
  instance_type = "t2.micro"
  tags          = { Name = each.key }
}

# count — conditional creation only
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count      = var.enable_monitoring ? 1 : 0
  alarm_name = "high-cpu-usage"
  threshold  = 80
}
```

## Modules

Use modules to encapsulate reusable infrastructure. Pin registry modules with `version`, git modules with `ref`:

```hcl
module "vpc" {
  source  = "hashicorp/vpc/aws"
  version = "~> 5.0"

  cidr_block  = var.vpc_cidr
  environment = var.environment
}
```

For module structure, naming, versioning, `moved` blocks, and input/output design, see [references/modules.md](references/modules.md).

## Security Best Practices

Apply these defaults when generating code:

- Enable encryption at rest (KMS/SSE)
- Configure private networking where applicable
- Apply least-privilege security groups and IAM policies
- Never hardcode credentials — use environment variables or IAM roles
- Mark sensitive outputs with `sensitive = true`
- Enable versioning on storage resources

## Version Constraints

Pin both Terraform and provider versions in `terraform.tf`:

```hcl
terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

Constraint operators: `= 1.0.0` (exact), `>= 1.0.0` (minimum), `~> 1.0` (allow rightmost increment), `>= 1.0, < 2.0` (range).

## Provider Configuration

```hcl
provider "aws" {
  region = "us-west-2"

  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = var.project_name
    }
  }
}
```

## Error Prevention

- Always use a remote backend with state locking for team projects
- Run `terraform plan -out=tfplan` and review before applying saved plans
- Use `lifecycle { prevent_destroy = true }` on critical stateful resources
- Prefer implicit dependencies over `depends_on`
- Never run concurrent applies against the same state file

For anti-patterns, dependency cycle resolution, state backend configs, `import`/`check` blocks, and recovery commands, see [references/error-prevention.md](references/error-prevention.md).

## Validation

Run before every commit:

```bash
terraform fmt -recursive    # Format
terraform validate          # Syntax + type check
```

Additional tools: `tflint` (linting), `checkov`/`tfsec` (security scanning).

## Code Review Checklist

- [ ] Formatted with `terraform fmt`
- [ ] Validated with `terraform validate`
- [ ] Files follow standard organization
- [ ] All variables have `type` and `description`
- [ ] All outputs have `description`
- [ ] Resource names: descriptive, lowercase, underscores, singular
- [ ] Version constraints pinned for Terraform and providers
- [ ] Sensitive values marked `sensitive = true`
- [ ] No hardcoded credentials or secrets
- [ ] Security defaults applied (encryption, private networking, least privilege)
- [ ] Modules pinned to specific versions

---

*Based on: [HashiCorp Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)*
