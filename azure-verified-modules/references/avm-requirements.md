# AVM Terraform Requirements — Full Reference

Detailed specifications for all Azure Verified Modules requirements. See [AVM Terraform Requirements](https://azure.github.io/Azure-Verified-Modules/specs/terraform/) for the latest upstream source.

## Table of Contents

- [Module Cross-Referencing](#module-cross-referencing)
- [Azure Provider Requirements](#azure-provider-requirements)
- [Code Style Standards](#code-style-standards)
- [Variable Requirements](#variable-requirements)
- [Output Requirements](#output-requirements)
- [Local Values Standards](#local-values-standards)
- [Terraform Configuration Requirements](#terraform-configuration-requirements)
- [Testing Requirements](#testing-requirements)
- [Documentation Requirements](#documentation-requirements)
- [Breaking Changes & Feature Management](#breaking-changes--feature-management)
- [Contribution Standards](#contribution-standards)

---

## Module Cross-Referencing

**Severity:** MUST | **Requirement:** TFFR1

When building Resource or Pattern modules, module owners **MAY** cross-reference other modules. However:

- Modules **MUST** be referenced using HashiCorp Terraform registry reference to a pinned version
  - Example: `source = "Azure/xxx/azurerm"` with `version = "1.2.3"`
- Modules **MUST NOT** use git references (e.g., `git::https://xxx.yyy/xxx.git` or `github.com/xxx/yyy`)
- Modules **MUST NOT** contain references to non-AVM modules

---

## Azure Provider Requirements

**Severity:** MUST | **Requirement:** TFFR3

Authors **MUST** only use the following Azure providers:

| Provider | Min Version | Max Version |
|----------|-------------|-------------|
| azapi    | >= 2.0      | < 3.0       |
| azurerm  | >= 4.0      | < 5.0       |

- Authors **MAY** select either Azurerm, Azapi, or both providers
- **MUST** use `required_providers` block to enforce provider versions
- **SHOULD** use pessimistic version constraint operator (`~>`)

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}
```

---

## Code Style Standards

### Lower snake_casing (TFNFR4 — MUST)

**MUST** use lower snake_casing for locals, variables, outputs, resources, and modules.

### Resource & Data Source Ordering (TFNFR6 — SHOULD)

- Resources that are depended on **SHOULD** come first
- Resources with dependencies **SHOULD** be defined close to each other

### Count & for_each Usage (TFNFR7 — MUST)

- Use `count` for conditional resource creation
- **MUST** use `map(xxx)` or `set(xxx)` as resource's `for_each` collection
- The map's key or set's element **MUST** be static literals

```hcl
resource "azurerm_subnet" "pair" {
  for_each             = var.subnet_map  # map(string)
  name                 = "${each.value}-pair"
  resource_group_name  = azurerm_resource_group.example.name
  virtual_network_name = azurerm_virtual_network.example.name
  address_prefixes     = ["10.0.1.0/24"]
}
```

### Resource & Data Block Internal Ordering (TFNFR8 — SHOULD)

1. **Meta-arguments (top)**: `provider`, `count`, `for_each`
2. **Arguments/blocks (middle, alphabetical)**: Required → Optional → Required nested → Optional nested
3. **Meta-arguments (bottom)**: `depends_on`, `lifecycle` (`create_before_destroy`, `ignore_changes`, `prevent_destroy`)

Separate sections with blank lines.

### Module Block Ordering (TFNFR9 — SHOULD)

1. **Top**: `source`, `version`, `count`, `for_each`
2. **Arguments (alphabetical)**: Required → Optional
3. **Bottom**: `depends_on`, `providers`

### Lifecycle ignore_changes Syntax (TFNFR10 — MUST)

`ignore_changes` **MUST NOT** be enclosed in double quotes.

### Null Comparison for Conditional Creation (TFNFR11 — SHOULD)

Wrap with `object` type to avoid "known after apply" issues:

```hcl
variable "security_group" {
  type = object({
    id = string
  })
  default = null
}
```

### Dynamic Blocks for Optional Nested Objects (TFNFR12 — MUST)

```hcl
dynamic "identity" {
  for_each = <condition> ? [<some_item>] : []
  content {
    # block content
  }
}
```

### Default Values with coalesce/try (TFNFR13 — SHOULD)

Use `coalesce(var.x, "default")` instead of ternary `var.x == null ? "default" : var.x`.

### Provider Declarations in Modules (TFNFR27 — MUST)

- `provider` **MUST NOT** be declared in modules (except for `configuration_aliases`)
- Provider configurations **SHOULD** be passed in by module users

---

## Variable Requirements

### Not Allowed Variables (TFNFR14 — MUST)

**MUST NOT** add variables like `enabled` or `module_depends_on` to control entire module. Boolean feature toggles for specific resources are acceptable.

### Variable Definition Order (TFNFR15 — SHOULD)

1. All required fields (alphabetical)
2. All optional fields (alphabetical)

### Variable Naming (TFNFR16 — SHOULD)

Feature switches **SHOULD** use positive statements: `xxx_enabled` instead of `xxx_disabled`.

### Descriptions (TFNFR17 — SHOULD)

`description` **SHOULD** precisely describe the parameter's purpose. For `object` types, use HEREDOC format.

### Types (TFNFR18 — MUST)

- `type` **MUST** be defined for every variable; **SHOULD** be as precise as possible
- `any` **MAY** only be used with adequate reasons
- Use `bool` instead of `string`/`number` for true/false; use concrete `object` instead of `map(any)`

### Sensitive Data (TFNFR19 — SHOULD)

If an `object` variable contains sensitive fields, the entire variable **SHOULD** be `sensitive = true`, or extract sensitive fields into separate variables.

### Non-Nullable Defaults for Collections (TFNFR20 — SHOULD)

`nullable` **SHOULD** be `false` for collection values used in loops.

### Discourage Nullability (TFNFR21 — MUST)

`nullable = true` **MUST** be avoided unless there's a specific semantic need.

### Avoid sensitive = false (TFNFR22 — MUST)

`sensitive = false` **MUST** be avoided (this is the default).

### Sensitive Default Values (TFNFR23 — MUST)

A default value **MUST NOT** be set for sensitive inputs.

### Deprecated Variables (TFNFR24 — MUST)

Move to `deprecated_variables.tf` with `DEPRECATED` prefix in description.

---

## Output Requirements

### Terraform Outputs (TFFR2 — SHOULD)

- **SHOULD NOT** output entire resource objects (contain sensitive data, schema changes)
- Output *computed* attributes as discrete outputs (anti-corruption layer pattern)
- **SHOULD NOT** output values that are already inputs (except `name`)
- Use `sensitive = true` for sensitive attributes
- For `for_each` resources, output computed attributes in a map structure

```hcl
output "foo" {
  description = "MyResource foo attribute"
  value       = azurerm_resource_myresource.foo
}

output "childresource_foos" {
  description = "MyResource children's foo attributes"
  value = {
    for key, value in azurerm_resource_mychildresource : key => value.foo
  }
}
```

### Sensitive Outputs (TFNFR29 — MUST)

**MUST** declare `sensitive = true` for confidential data.

### Deprecated Outputs (TFNFR30 — MUST)

Move to `deprecated_outputs.tf`; define new outputs in `outputs.tf`.

---

## Local Values Standards

- `locals.tf` **SHOULD** only contain `locals` blocks (TFNFR31)
- Expressions **MUST** be arranged alphabetically (TFNFR32)
- Use precise types (TFNFR33)

---

## Terraform Configuration Requirements

### Version Requirements (TFNFR25 — MUST)

- **MUST** contain one `terraform` block with `required_version` as first line
- **SHOULD** use `~> #.#` or `>= #.#.#, < #.#.#` format

```hcl
terraform {
  required_version = "~> 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
```

### Providers in required_providers (TFNFR26 — MUST)

- Each provider **MUST** specify `source` and `version`
- Providers **SHOULD** be sorted alphabetically
- `source` **MUST** be `namespace/name` format

---

## Testing Requirements

### Test Tooling (TFNFR5 — MUST)

Required: Terraform (`validate/fmt/test`), terrafmt, Checkov, tflint (azurerm ruleset). Optional: Go.

### Test Provider Configuration (TFNFR36 — SHOULD)

Set `prevent_deletion_if_contains_resources = false` in test provider configs.

---

## Documentation Requirements

### Module Documentation (TFNFR2 — MUST)

- **MUST** use [Terraform Docs](https://github.com/terraform-docs/terraform-docs) for auto-generation
- `.terraform-docs.yml` **MUST** be present in module root

---

## Breaking Changes & Feature Management

### Feature Toggles (TFNFR34 — MUST)

New resources in minor/patch versions **MUST** have a toggle variable:

```hcl
variable "create_route_table" {
  type     = bool
  default  = false
  nullable = false
}

resource "azurerm_route_table" "this" {
  count = var.create_route_table ? 1 : 0
}
```

### Potential Breaking Changes (TFNFR35 — MUST)

**Resource blocks:** Adding resource without conditional, adding arguments with non-defaults, adding nested blocks without `dynamic`, renaming without `moved`, changing `count`↔`for_each`.

**Variable/Output blocks:** Deleting/renaming variables, changing `type`/`default`/`nullable`/`sensitive`, adding variables without `default`, deleting outputs, changing output `value`/`sensitive`.

---

## Contribution Standards

### Branch Protection (TFNFR3 — MUST)

On default branch: Require PR, require approval of latest push, dismiss stale approvals, require linear history, prevent force pushes, no deletions, require CODEOWNERS review, enforce for administrators.
