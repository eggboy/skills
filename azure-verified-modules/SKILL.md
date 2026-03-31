---
name: azure-verified-modules
description: Develop, review, and consume certified Azure Verified Modules (AVM) for Terraform following AVM requirements and best practices. Use when creating AVM-compliant modules, or configuring VNet injection, subnet delegation, or NSG rules in Terraform. DO NOT use for generic Terraform style guidance (use terraform-style-guide), non-AVM community modules, or non-Azure providers.
---

# Azure Verified Modules (AVM) — Terraform

Core workflow and checklists for AVM-compliant Terraform modules.

**Upstream source:** [AVM Terraform Requirements](https://azure.github.io/Azure-Verified-Modules/specs/terraform/)

| Reference | Content |
|---|---|
| [references/avm-requirements.md](references/avm-requirements.md) | Full TFFR/TFNFR requirement specs |
| [references/examples.md](references/examples.md) | Bad-vs-good HCL patterns |
| [references/vnet-guide.md](references/vnet-guide.md) | VNet injection workflow + tier-specific examples |

---

## Quick Reference — Key Rules

### Module References (MUST)

- Registry source with pinned version: `source = "Azure/xxx/azurerm"` + `version = "1.2.3"`
- No git references. No non-AVM modules.

### Providers (MUST)

- `azurerm ~> 4.0` and/or `azapi ~> 2.0` only
- No `provider` blocks in modules (except `configuration_aliases`)

### Code Style (MUST)

- Lower `snake_casing` everywhere
- `for_each` with `map()` or `set()` using static keys only
- `ignore_changes` **not quoted** (e.g., `[tags]` not `["tags"]`)
- Dynamic blocks for conditional nested objects
- Block ordering: meta-args top → arguments alphabetical → meta-args bottom
- `coalesce()`/`try()` for defaults instead of ternary

### Variables (MUST)

- No `enabled` / `module_depends_on` variables
- Every variable has `type` and `description`; required first (alphabetical), then optional
- Collections: `nullable = false`
- No `sensitive = false` (it's the default); no default values for sensitive inputs
- Deprecated → move to `deprecated_variables.tf` with `DEPRECATED` prefix

### Outputs (MUST)

- Output only discrete computed attributes (not entire resource objects)
- `sensitive = true` for confidential data
- Deprecated → move to `deprecated_outputs.tf`

### Breaking Changes (MUST)

- New resources in minor/patch: feature toggle variable with `default = false`
- Renamed resources: `moved` blocks (no destroy/recreate)
- Review all changes against [TFNFR35 breaking change list](references/avm-requirements.md#breaking-changes--feature-management)

---

## VNet Injection — Mandatory Verification

Verify exact networking requirements from official docs before writing any VNet injection, subnet delegation, or NSG config. Requirements differ **across tiers/SKUs within the same service** — wrong config leads to cryptic failures (`MethodNotAllowedInPricingTier`), subnet delegation conflicts, or missing NSG rules.

Follow the step-by-step verification workflow and tier-specific HCL examples in [references/vnet-guide.md](references/vnet-guide.md).

---

## Quick Compliance Check

Before submitting, verify:

- **Sources & providers** — Registry-pinned sources, correct provider versions, `.terraform-docs.yml`, CODEOWNERS
- **Code style** — snake_casing, block ordering, dynamic blocks, static `for_each` keys
- **Variables/outputs** — AVM conventions (ordering, typing, sensitivity, deprecation)
- **VNet config** — Verified from official docs for exact tier/SKU ([full checklist](references/vnet-guide.md#checklist))
- **Breaking changes** — New resources gated by feature toggle; changes reviewed per TFNFR35
- **Tests** — terraform validate/fmt/test, terrafmt, Checkov, tflint

For full requirement details, see [references/avm-requirements.md](references/avm-requirements.md).
For bad-vs-good HCL examples, see [references/examples.md](references/examples.md).
