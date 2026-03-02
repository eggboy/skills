---
name: azure-naming-convention
description: Generate compliant Azure resource names following Microsoft Cloud Adoption Framework (CAF) best practices. Use when naming any Azure resource, generating IaC (Bicep, Terraform, ARM), scaffolding Azure projects, or reviewing existing resource names for compliance. Triggers on: Azure resource naming, name Azure resources, naming convention, resource abbreviation, CAF naming.
---

# Azure Naming Convention

Generate Azure resource names following the Microsoft Cloud Adoption Framework naming convention.

**Sources:**
- [Resource naming](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming)
- [Resource abbreviations](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations)

## Naming Format

The standard pattern is:

```
<resource-abbreviation>-<workload>-<environment>-<region>-<instance>
```

Use hyphens `-` as delimiters. Omit optional components when not needed.

### Naming Components

| Component | Required | Description | Examples |
|-----------|----------|-------------|----------|
| Resource type | Yes | CAF abbreviation for the resource type | `rg`, `vm`, `st`, `app`, `aks` |
| Workload | Yes | Application, project, or workload name | `navigator`, `emissions`, `sharepoint` |
| Environment | Yes | Deployment stage | `prod`, `dev`, `qa`, `stage`, `test` |
| Region | Situational | Azure region (use short form) | `eastus`, `westus2`, `westeu`, `southeastasia` |
| Instance | Situational | Zero-padded instance number | `001`, `002` |

### Component Order

Place the resource abbreviation **first** so resources sort by type. Follow with workload, environment, region, and instance:

```
<abbreviation>-<workload>-<environment>[-<region>][-<instance>]
```

## Key Rules

1. **Resource abbreviation lookup** — Look up the correct abbreviation from [references/abbreviations.md](references/abbreviations.md).
2. **No special characters in restricted resources** — Storage accounts, container registries, and Data Lake Storage **cannot** use hyphens. Concatenate components directly: `stnavigatorprod001`, `crnavigatorprod001`.
3. **Length limits** — Many Azure resources have strict max-length constraints. **Always** check the table below and truncate the workload component if needed. See [references/naming-rules.md](references/naming-rules.md) for full constraints.
4. **Lowercase** — Use lowercase for all resource names. Some resources (e.g., storage accounts) enforce this.
5. **Instance numbering** — Use three-digit zero-padded numbers (`001`, `002`) unless the resource is a singleton.
6. **Globally unique names** — Resources with global scope (storage accounts, web apps, Key Vaults, Cosmos DB) must be globally unique. Append instance numbers or short random suffixes when necessary.
7. **Start/end character rules** — Many resources must start with a letter and end with a letter or number. Key Vaults and storage accounts cannot contain consecutive hyphens.

## Length Limits Quick Reference

Resources with short max lengths that commonly cause naming failures:

| Resource | Max Length | Allowed Characters | Hyphens? | Scope |
|----------|-----------|-------------------|----------|-------|
| Storage account | **3-24** | Lowercase + numbers only | No | Global |
| Key Vault | **3-24** | Alphanumerics + hyphens, start with letter, no consecutive hyphens | Yes | Global |
| VM (Windows host) | **1-15** | Alphanumerics + hyphens | Yes | Resource group |
| VM (Linux host) | **1-64** | Alphanumerics + hyphens | Yes | Resource group |
| Data Lake Storage | **3-24** | Lowercase + numbers only | No | Global |
| Container registry | **5-50** | Alphanumerics only | No | Global |
| Container app | **2-32** | Lowercase + numbers + hyphens | Yes | Resource group |
| AKS cluster | **1-63** | Alphanumerics + underscores + hyphens | Yes | Resource group |
| AKS node pool (Linux) | **1-12** | Lowercase + numbers, start with letter | No | Cluster |
| AKS node pool (Windows) | **1-6** | Lowercase + numbers, start with letter | No | Cluster |
| Cosmos DB account | **3-44** | Lowercase + numbers + hyphens | Yes | Global |
| SQL server | **1-63** | Lowercase + numbers + hyphens | Yes | Global |
| SQL database | **1-128** | Most characters except `<>*%&:\/?` | Yes | Server |
| Redis cache | **1-63** | Alphanumerics + hyphens, no consecutive hyphens | Yes | Global |
| Web app / Function app | **2-60** | Alphanumerics + hyphens | Yes | Global |
| App Service plan | **1-60** | Alphanumerics + hyphens | Yes | Resource group |
| Service Bus namespace | **6-50** | Alphanumerics + hyphens | Yes | Global |
| Event Hub namespace | **6-50** | Alphanumerics + hyphens | Yes | Global |
| API Management | **1-50** | Alphanumerics + hyphens | Yes | Global |
| Log Analytics workspace | **4-63** | Alphanumerics + hyphens | Yes | Resource group |
| Application Insights | **1-260** | Most characters | Yes | Resource group |
| Managed identity | **3-128** | Alphanumerics + hyphens + underscores | Yes | Resource group |
| Resource group | **1-90** | Alphanumerics + underscores + hyphens + periods + parentheses | Yes | Subscription |
| Virtual network | **2-64** | Alphanumerics + underscores + periods + hyphens | Yes | Resource group |
| Subnet | **1-80** | Alphanumerics + underscores + periods + hyphens | Yes | VNet |
| NSG | **1-80** | Alphanumerics + underscores + periods + hyphens | Yes | Resource group |
| Public IP | **1-80** | Alphanumerics + underscores + periods + hyphens | Yes | Resource group |
| App Configuration | **5-50** | Alphanumerics + hyphens | Yes | Global |
| Service Fabric cluster | **4-23** | Lowercase + numbers + hyphens | Yes | Region |

For the **complete** naming rules (all resources, valid characters, start/end constraints), see [references/naming-rules.md](references/naming-rules.md).

## Scope Reference

| Scope | Uniqueness Requirement | Typical Resources |
|-------|------------------------|-------------------|
| Global | Unique across all of Azure | Storage accounts, web apps, function apps, Cosmos DB, Key Vaults, Container Registries |
| Resource group | Unique within the resource group | VMs, NICs, NSGs, VNets, managed disks |
| Resource | Unique within the parent resource | Subnets (within VNet), SQL databases (within SQL server) |

## Examples by Category

### Compute and Web

```
vm-sql-prod-001              # Virtual machine
vmss-web-prod-001            # VM scale set
app-navigator-prod-001       # Web app
func-payments-prod-001       # Function app
asp-navigator-prod           # App Service plan
```

### Containers

```
aks-navigator-prod-001       # AKS cluster
crnavigatorprod001           # Container registry (no hyphens)
ca-payments-prod             # Container app
cae-shared-prod              # Container apps environment
```

### Networking

```
vnet-shared-eastus2-001      # Virtual network
snet-web-eastus2-001         # Subnet
nsg-weballow-001             # Network security group
pip-hadoop-prod-westus-001   # Public IP
lbe-navigator-prod-001       # Load balancer (external)
agw-shared-prod              # Application gateway
afw-shared-prod              # Azure Firewall
```

### Databases

```
sql-navigator-prod           # Azure SQL server
sqldb-users-prod             # Azure SQL database
cosmos-navigator-prod        # Cosmos DB
redis-sessions-prod          # Azure Cache for Redis
psql-navigator-prod          # PostgreSQL
mysql-navigator-prod         # MySQL
```

### Storage

```
stnavigatordata001           # Storage account (no hyphens, max 24 chars)
dlsnavigatorprod             # Data Lake Storage (no hyphens)
share-config                 # File share
```

### Management and Governance

```
rg-navigator-prod            # Resource group
log-navigator-prod           # Log Analytics workspace
appi-navigator-prod          # Application Insights
kv-navigator-prod            # Key Vault
id-navigator-prod-001        # Managed identity
```

### AI and Machine Learning

```
srch-navigator-prod          # AI Search
oai-navigator-prod           # Azure OpenAI
mlw-navigator-prod           # ML workspace
```

### Integration

```
apim-navigator-prod          # API Management
sbns-navigator-prod          # Service Bus namespace
sbq-orders                   # Service Bus queue
logic-payments-prod          # Logic app
```

## IaC Integration

When generating Terraform, Bicep, or ARM templates, apply these conventions to all resource names. Use variables/parameters for workload, environment, and region components:

**Terraform:**
```hcl
locals {
  name_prefix = "${var.workload}-${var.environment}"
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_prefix}"
  location = var.location
}
```

**Bicep:**
```bicep
param workload string
param environment string

var namePrefix = '${workload}-${environment}'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${namePrefix}'
  location: deployment().location
}
```

