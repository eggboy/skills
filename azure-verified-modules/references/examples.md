# AVM Examples — Bad vs Good Patterns

Side-by-side HCL examples demonstrating AVM-compliant patterns. Each section shows the **wrong** way first, then the **correct** way.

## Table of Contents

- [Module References](#module-references)
- [Block Ordering](#block-ordering)
- [ignore_changes Quoting](#ignore_changes-quoting)
- [for_each with Static Keys](#for_each-with-static-keys)
- [Dynamic Blocks](#dynamic-blocks)
- [Outputs — Discrete vs Leaking](#outputs--discrete-vs-leaking)
- [Sensitive Variables](#sensitive-variables)
- [Feature Toggle for New Resources](#feature-toggle-for-new-resources)
- [Moved Blocks for Resource Renames](#moved-blocks-for-resource-renames)
- [Deprecated Variables & Outputs](#deprecated-variables--outputs)
- [Variable Ordering](#variable-ordering)
- [coalesce/try Instead of Ternary](#coalescetry-instead-of-ternary)

---

## Module References

```hcl
# ❌ BAD — git reference
module "network" {
  source = "git::https://github.com/Azure/terraform-azurerm-network.git?ref=v3.0.0"
}

# ❌ BAD — non-AVM module
module "network" {
  source  = "some-org/network/azurerm"
  version = "2.0.0"
}
```

```hcl
# ✅ GOOD — registry source with pinned version
module "network" {
  source  = "Azure/network/azurerm"
  version = "4.1.0"
}
```

---

## Block Ordering

```hcl
# ❌ BAD — meta-args scattered, arguments not alphabetical
resource "azurerm_linux_virtual_machine" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  for_each            = var.vm_map          # meta-arg should be at top
  location            = var.location
  size                = var.size
  admin_username      = var.admin_username
  depends_on          = [azurerm_subnet.this]
  network_interface_ids = [each.value.nic_id]

  lifecycle {                               # lifecycle mixed in with args
    ignore_changes = ["tags"]               # ❌ also: quoted ignore_changes
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }
}
```

```hcl
# ✅ GOOD — meta-args top, args alphabetical, meta-args bottom
resource "azurerm_linux_virtual_machine" "this" {
  for_each = var.vm_map

  admin_username        = var.admin_username
  location              = var.location
  name                  = each.value.name
  network_interface_ids = [each.value.nic_id]
  resource_group_name   = var.resource_group_name
  size                  = var.size

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  depends_on = [azurerm_subnet.this]

  lifecycle {
    ignore_changes = [tags]  # ✅ no quotes
  }
}
```

---

## ignore_changes Quoting

```hcl
# ❌ BAD — quoted
lifecycle {
  ignore_changes = ["tags", "identity"]
}
```

```hcl
# ✅ GOOD — unquoted (TFNFR10)
lifecycle {
  ignore_changes = [tags, identity]
}
```

---

## for_each with Static Keys

```hcl
# ❌ BAD — for_each on a list (non-static keys, index-based)
resource "azurerm_subnet" "this" {
  for_each = toset(var.subnet_list)  # list elements can shift
  name     = each.value
}

# ❌ BAD — for_each on computed values
resource "azurerm_subnet" "this" {
  for_each = { for s in var.subnets : s.name => s }  # keys may change
  name     = each.value.name
}
```

```hcl
# ✅ GOOD — map with static string keys
variable "subnets" {
  type = map(object({
    address_prefix = string
    delegation     = optional(string)
  }))
}

resource "azurerm_subnet" "this" {
  for_each             = var.subnets  # map keys are static literals
  name                 = each.key
  address_prefixes     = [each.value.address_prefix]
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
}
```

---

## Dynamic Blocks

```hcl
# ❌ BAD — hardcoded nested block (always created even when not needed)
resource "azurerm_linux_virtual_machine" "this" {
  # ...
  identity {
    type = "SystemAssigned"
  }
}
```

```hcl
# ✅ GOOD — dynamic block for conditional nested object (TFNFR12)
resource "azurerm_linux_virtual_machine" "this" {
  # ...
  dynamic "identity" {
    for_each = var.identity_type != null ? [var.identity_type] : []
    content {
      type = identity.value
    }
  }
}
```

---

## Outputs — Discrete vs Leaking

```hcl
# ❌ BAD — leaking entire resource object (sensitive data, schema coupling)
output "virtual_network" {
  value = azurerm_virtual_network.this
}
```

```hcl
# ✅ GOOD — discrete computed attributes only (TFFR2)
output "virtual_network_id" {
  description = "The ID of the virtual network."
  value       = azurerm_virtual_network.this.id
}

output "virtual_network_name" {
  description = "The name of the virtual network."
  value       = azurerm_virtual_network.this.name
}

# ✅ GOOD — map structure for for_each resources
output "subnet_ids" {
  description = "Map of subnet name to subnet ID."
  value = {
    for key, subnet in azurerm_subnet.this : key => subnet.id
  }
}
```

---

## Sensitive Variables

```hcl
# ❌ BAD — sensitive = false is redundant (TFNFR22)
variable "resource_group_name" {
  type        = string
  sensitive   = false  # this is already the default
  description = "The resource group name."
}

# ❌ BAD — default value on sensitive input (TFNFR23)
variable "admin_password" {
  type      = string
  sensitive = true
  default   = "P@ssw0rd123"  # MUST NOT have default
}
```

```hcl
# ✅ GOOD — sensitive input with no default
variable "admin_password" {
  type        = string
  sensitive   = true
  description = "The admin password for the VM."
}
```

---

## Feature Toggle for New Resources

```hcl
# ❌ BAD — new resource in minor version with no toggle (breaking change)
resource "azurerm_route_table" "this" {
  name                = "${var.name}-rt"
  location            = var.location
  resource_group_name = var.resource_group_name
}
```

```hcl
# ✅ GOOD — feature toggle with default = false (TFNFR34)
variable "create_route_table" {
  type        = bool
  default     = false
  nullable    = false
  description = "Whether to create a route table. Added in v1.2.0."
}

resource "azurerm_route_table" "this" {
  count = var.create_route_table ? 1 : 0

  name                = "${var.name}-rt"
  location            = var.location
  resource_group_name = var.resource_group_name
}
```

---

## Moved Blocks for Resource Renames

```hcl
# ❌ BAD — renamed resource without moved block (destroys + recreates)
# Was: azurerm_virtual_network.main
# Now:
resource "azurerm_virtual_network" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
}
# Users upgrading will see: destroy "main", create "this" — DATA LOSS
```

```hcl
# ✅ GOOD — moved block preserves state (no destroy/recreate)
moved {
  from = azurerm_virtual_network.main
  to   = azurerm_virtual_network.this
}

resource "azurerm_virtual_network" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space
}
```

---

## Deprecated Variables & Outputs

```hcl
# ❌ BAD — deprecated variable left in variables.tf with no warning
variable "vnet_name" {
  type        = string
  default     = ""
  description = "The VNet name."
}
```

```hcl
# ✅ GOOD — in deprecated_variables.tf with DEPRECATED prefix (TFNFR24)
variable "vnet_name" {
  type        = string
  default     = ""
  description = "DEPRECATED: Use `virtual_network_name` instead. Will be removed in v3.0."
}
```

```hcl
# ✅ GOOD — in deprecated_outputs.tf with DEPRECATED prefix (TFNFR30)
output "vnet_id" {
  description = "DEPRECATED: Use `virtual_network_id` instead. Will be removed in v3.0."
  value       = azurerm_virtual_network.this.id
}
```

---

## Variable Ordering

```hcl
# ❌ BAD — mixed required and optional, not alphabetical
variable "tags" {
  type    = map(string)
  default = {}
}

variable "name" {
  type = string  # required
}

variable "location" {
  type = string  # required
}

variable "sku" {
  type    = string
  default = "Standard"
}
```

```hcl
# ✅ GOOD — required first (alphabetical), then optional (alphabetical) (TFNFR15)
# --- Required ---

variable "location" {
  type        = string
  description = "The Azure region for all resources."
}

variable "name" {
  type        = string
  description = "The name prefix for all resources."
}

# --- Optional ---

variable "sku" {
  type        = string
  default     = "Standard"
  description = "The SKU tier."
}

variable "tags" {
  type        = map(string)
  default     = {}
  nullable    = false
  description = "A map of tags to apply to all resources."
}
```

---

## coalesce/try Instead of Ternary

```hcl
# ❌ BAD — verbose ternary
locals {
  effective_name = var.custom_name == null ? var.default_name : var.custom_name
}
```

```hcl
# ✅ GOOD — coalesce (TFNFR13)
locals {
  effective_name = coalesce(var.custom_name, var.default_name)
}
```
