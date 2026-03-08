# VNet Injection & Subnet Configuration Guide

Detailed verification workflow for VNet injection, subnet delegation, and NSG configuration in AVM Terraform modules.

**Key principle:** Requirements differ across services **and across tiers/SKUs within the same service**. Never assume — always verify from official docs.

## Table of Contents

- [Mandatory Verification Workflow](#mandatory-verification-workflow)
- [Tier-Specific Pitfall: APIM Example](#tier-specific-pitfall-apim-example)
- [Common VNet Services Quick Reference](#common-vnet-services-quick-reference)
- [Checklist](#checklist)

---

## Mandatory Verification Workflow

### Step 1: Search Docs (SKU/tier-specific)

Use `microsoft_docs_search` with the **specific SKU/tier** in the query.

```
# ✅ GOOD — tier-specific query
microsoft_docs_search("API Management Premium v2 VNet injection")
microsoft_docs_search("Azure Cache for Redis Enterprise VNet")

# ❌ BAD — too generic (will return wrong tier's config)
microsoft_docs_search("API Management VNet")
microsoft_docs_search("Redis VNet injection")
```

### Step 2: Fetch and Extract

Use `microsoft_docs_fetch` on the result URL. Extract these exact fields:

| Field | What to look for | Example |
|---|---|---|
| **Subnet delegation** | Exact `service_delegation` name, or `None` | `Microsoft.Web/hostingEnvironments` |
| **Subnet sizing** | Minimum CIDR / minimum IPs | `/27` (32 IPs) |
| **NSG inbound rules** | Required ports, protocols, service tags | `3443/TCP from ApiManagement` |
| **NSG outbound rules** | Required ports, protocols, service tags | `443/TCP to Storage, AzureKeyVault` |
| **Tier differences** | How requirements change across SKUs | Classic vs v2 have different delegation |
| **Unsupported operations** | API methods/properties blocked on tier | `virtualNetworkConfiguration` on v2 |
| **DNS** | Private DNS zones, custom DNS needed | `privatelink.redis.cache.windows.net` |

### Step 3: Cross-Check Terraform

Verify **every** Terraform parameter matches the extracted docs:
- `service_delegation.name` matches exactly
- `address_prefixes` meets minimum CIDR
- All NSG rules present (both inbound and outbound)
- No unsupported API properties used for the target tier

---

## Tier-Specific Pitfall: APIM Example

This is the canonical example of why tier-specific verification matters.

### APIM Classic Premium

```hcl
# Classic Premium: NO subnet delegation, specific inbound ports
resource "azurerm_subnet" "apim" {
  name                 = "snet-apim"
  address_prefixes     = ["/27"]  # minimum
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  # No delegation block — Classic doesn't use delegation
}

resource "azurerm_network_security_group" "apim" {
  name                = "nsg-apim"
  location            = var.location
  resource_group_name = var.resource_group_name

  # Required inbound: Management endpoint
  security_rule {
    name                       = "AllowAPIMManagement"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3443"
    source_address_prefix      = "ApiManagement"
    destination_address_prefix = "VirtualNetwork"
  }

  # Required inbound: Load balancer health probe
  security_rule {
    name                       = "AllowAzureLoadBalancer"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "6390"
    source_address_prefix      = "AzureLoadBalancer"
    destination_address_prefix = "VirtualNetwork"
  }
}
```

### APIM Premium v2

```hcl
# Premium v2: REQUIRES delegation, different ports, different approach
resource "azurerm_subnet" "apim_v2" {
  name                 = "snet-apim-v2"
  address_prefixes     = ["/27"]
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name

  # ⚠️ v2 REQUIRES this specific delegation
  delegation {
    name = "apim-delegation"
    service_delegation {
      name = "Microsoft.Web/hostingEnvironments"
    }
  }
}

resource "azurerm_network_security_group" "apim_v2" {
  name                = "nsg-apim-v2"
  location            = var.location
  resource_group_name = var.resource_group_name

  # v2 requires outbound to Storage and KeyVault on 443
  security_rule {
    name                       = "AllowStorageOutbound"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "Storage"
  }

  security_rule {
    name                       = "AllowKeyVaultOutbound"
    priority                   = 110
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "AzureKeyVault"
  }
}

# ⚠️ Do NOT use virtualNetworkConfiguration on v2 — it's unsupported
# Use the subnet ID directly on the API Management resource instead
```

**Using Classic config for v2 (or vice versa) will fail with `MethodNotAllowedInPricingTier`.**

---

## Common VNet Services Quick Reference

| Service | Delegation Required | Min CIDR | Key Ports |
|---|---|---|---|
| APIM Classic | None | /27 | IN: 3443, 6390 |
| APIM v2 | `Microsoft.Web/hostingEnvironments` | /27 | OUT: 443 (Storage, KV) |
| App Service | `Microsoft.Web/serverFarms` | /26 | OUT: 443 |
| Container Apps | `Microsoft.App/environments` | /23 | Varies |
| Azure SQL MI | `Microsoft.Sql/managedInstances` | /27 | IN: 9000-9999, 1433, 11000-11999 |
| Azure Databricks | `Microsoft.Databricks/workspaces` | /26 (×2) | IN/OUT: various |

> **Always verify** — this table is a starting point. Use `microsoft_docs_search` + `microsoft_docs_fetch` for the authoritative source.

---

## Checklist

- [ ] Official docs searched for **exact service tier/SKU**
- [ ] Subnet delegation matches documented `service_delegation` name exactly
- [ ] Subnet CIDR meets documented minimum
- [ ] All required NSG inbound rules present with correct ports/service tags
- [ ] All required NSG outbound rules present with correct ports/service tags
- [ ] No unsupported API operations/properties for target tier
- [ ] Private DNS zones configured per docs
- [ ] Cross-checked every Terraform parameter against docs
