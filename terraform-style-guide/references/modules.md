# Modules

## Table of Contents

- [Module Structure](#module-structure)
- [Consuming Modules](#consuming-modules)
- [Creating Reusable Modules](#creating-reusable-modules)
- [Module Versioning](#module-versioning)

## Module Structure

```
modules/
└── vpc/
    ├── README.md
    ├── main.tf          # Resources
    ├── variables.tf     # Inputs (alphabetical, all with type + description)
    ├── outputs.tf       # Outputs (alphabetical, all with description)
    └── versions.tf      # Required providers and Terraform version
```

Keep modules focused on a single responsibility. Avoid "god modules" that manage unrelated resources.

## Consuming Modules

### Registry Modules

Pin with `version` using pessimistic constraint:

```hcl
module "vpc" {
  source  = "hashicorp/consul/aws"
  version = "~> 1.2"

  # Pass all required variables explicitly
  environment = var.environment
  cidr_block  = var.vpc_cidr
}
```

### Git Modules

Pin with `ref` to a tag (never a branch):

```hcl
module "vpc" {
  source = "git::https://example.com/network.git//modules/vpc?ref=v1.2.0"
}
```

### Local Modules

Use relative paths:

```hcl
module "vpc" {
  source = "../modules/vpc"
}
```

## Creating Reusable Modules

### Input Design

- Expose only what consumers need to configure
- Provide sensible defaults for optional inputs
- Use `validation` blocks for constrained inputs
- Group related inputs with a common prefix (e.g., `db_instance_type`, `db_storage_size`)

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t[23]\\.", var.instance_type))
    error_message = "Only t2 or t3 instance types are allowed."
  }
}
```

### Output Design

- Output all attributes consumers may need (IDs, ARNs, endpoints)
- Use `description` on every output
- Mark sensitive outputs with `sensitive = true`

```hcl
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}
```

### Module Naming

- Name: `terraform-<PROVIDER>-<PURPOSE>` (e.g., `terraform-aws-vpc`)
- Internal resource names: use `this` or `main` when the module creates one primary resource

## Module Versioning

Follow semantic versioning (SemVer):

- **Major** (1.0 → 2.0): Breaking changes to inputs/outputs
- **Minor** (1.0 → 1.1): New features, backward-compatible
- **Patch** (1.0.0 → 1.0.1): Bug fixes only

### Refactoring with moved Blocks

Use `moved` blocks to rename resources without destroying them:

```hcl
# Rename a resource
moved {
  from = aws_instance.web
  to   = aws_instance.app
}

# Migrate from count to for_each
moved {
  from = aws_instance.web[0]
  to   = aws_instance.web["primary"]
}

# Migrate from single to module
moved {
  from = aws_instance.web
  to   = module.web.aws_instance.this
}
```

Always include `moved` blocks in the same release that renames or restructures resources. Remove `moved` blocks after all consumers have upgraded.
