# Dynamic Resource Creation

## Decision Guide

Use this flowchart to choose the right iteration mechanism:

```
Need to create multiple similar resources?
├─ YES → Are instances identified by meaningful names/keys?
│        ├─ YES → Use for_each with a map or set
│        └─ NO  → Is the count purely numeric with no reordering risk?
│                 ├─ YES → Use count
│                 └─ NO  → Convert to for_each with stable keys
├─ Need to conditionally create a single resource?
│  └─ Use count = var.enabled ? 1 : 0
└─ Need to repeat nested blocks within a resource?
   └─ Use dynamic blocks
```

## for_each (Default Choice)

Use `for_each` when each instance has a stable identity. Removing an item only affects that item — other instances are untouched.

```hcl
variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
  default = {
    public  = { cidr = "10.0.1.0/24", az = "us-west-2a" }
    private = { cidr = "10.0.2.0/24", az = "us-west-2b" }
  }
}

resource "aws_subnet" "this" {
  for_each          = var.subnets
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = { Name = each.key }
}

# Reference: aws_subnet.this["public"].id
```

### for_each with Sets

```hcl
resource "aws_iam_user" "admin" {
  for_each = toset(["alice", "bob", "carol"])
  name     = each.key
}
```

### for_each Gotchas

- `for_each` keys must be known at plan time — cannot depend on resource attributes
- Use `toset()` to convert lists; duplicates cause errors
- Empty maps/sets create zero instances (safe)

## count

Use `count` only for conditional creation or truly numeric, position-stable resources:

```hcl
# Conditional creation — the primary use case for count
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name = "high-cpu"
  threshold  = 80
}

# Reference: aws_cloudwatch_metric_alarm.cpu[0].arn (use with one_of)
# Or: one(aws_cloudwatch_metric_alarm.cpu[*].arn)
```

### count Pitfalls

- Removing an item from the middle of a list shifts all subsequent indices — causes unnecessary destroy/recreate
- `count.index` makes resources fragile to reordering
- Prefer `for_each` whenever instances have meaningful names

## dynamic Blocks

Use `dynamic` to generate repeated nested blocks within a resource:

```hcl
variable "ingress_rules" {
  type = list(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
}

resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
}
```

### dynamic Block Rules

- Never nest `dynamic` blocks more than one level deep — extract to a module instead
- Always set the iterator name explicitly when nesting to avoid shadowing
- Prefer static blocks when the number of blocks is small and fixed
