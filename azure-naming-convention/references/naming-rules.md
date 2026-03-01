# Azure Resource Naming Rules

Complete naming rules from the [official Microsoft documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules).

Grep for a resource type name (e.g., "Key Vault", "Storage account") to find its constraints.

## General Rules

- Resource and resource group names are **case-insensitive** unless noted otherwise.
- Resources with public endpoints **cannot** use reserved words or trademarks.
- Do **not** use `#` in resource names (breaks URL parsing in ARM requests).

## AI + Machine Learning

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Cognitive Services accounts | Resource group | 2-64 | Alphanumerics and hyphens. Start/end with alphanumeric. |
| ML Services workspace | Resource group | 3-33 | Alphanumerics, hyphens, and underscores |
| ML compute instance | Workspace | 3-24 | Alphanumerics and hyphens |
| AI Search | Global | 2-60 | Lowercase, numbers, hyphens. Start with letter. No consecutive hyphens. |

## Analytics and IoT

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Analysis Services server | Resource group | 3-63 | Lowercase letters and numbers. Start with lowercase letter. |
| Databricks workspace | Resource group | 3-64 | Alphanumerics, underscores, and hyphens |
| Data Explorer cluster | Global | 4-22 | Lowercase letters and numbers. Start with a letter. |
| Data Factory | Global | 3-63 | Alphanumerics and hyphens. Start/end with alphanumeric. |
| Data Lake Store account | Global | 3-24 | Lowercase letters and numbers |
| Event Hubs namespace | Global | 6-50 | Alphanumerics and hyphens. Start with letter, end with letter/number. |
| Event Hub | Namespace | 1-256 | Alphanumerics, periods, hyphens, underscores. Start/end with alphanumeric. |
| Event Grid domain | Resource group | 3-50 | Alphanumerics and hyphens |
| HDInsight cluster | Global | 3-59 | Alphanumerics and hyphens. Start/end with letter/number. |
| IoT Hub | Global | 3-50 | Alphanumerics and hyphens. Cannot end with hyphen. |
| Stream Analytics job | Resource group | 3-63 | Alphanumerics, hyphens, and underscores |
| Synapse workspace | Global | 1-50 | Lowercase, hyphens, numbers. Start/end with letter/number. Cannot contain `-ondemand`. |
| Synapse Spark Pool | Workspace | 1-15 | Letters and numbers. Start with letter. |
| Fabric Capacity | Region | 3-63 | Lowercase letters or numbers. Start with lowercase letter. |

## Compute and Web

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| App Service plan | Resource group | 1-60 | Alphanumerics, hyphens, Punycode |
| Web app | Global | 2-60 | Alphanumerics, hyphens, Punycode. No start/end hyphen. |
| Function app | Global | 2-60 | Same as web app |
| Static web app | Resource group | 2-60 | Alphanumerics and hyphens |
| Virtual machine (host) | Resource group | 1-15 (Win) / 1-64 (Linux) | No spaces or `~ ! @ # $ % ^ & * ( ) = + _ [ ] { } \| ; : . ' " , < > / ?`. Win: no periods, no trailing hyphen. Linux: no trailing period/hyphen. |
| VM scale set (host) | Resource group | 1-15 (Win) / 1-64 (Linux) | Same as VM. No leading underscore, no trailing period/hyphen. |
| Availability set | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens |
| Managed disk | Resource group | 1-80 | Alphanumerics, underscores, hyphens |
| Snapshot | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens |
| Gallery | Resource group | 1-80 | Alphanumerics and periods |
| Batch account | Region | 3-24 | Lowercase letters and numbers |
| Cloud service | Resource group | 1-15 | Same character restrictions as VM |
| Notification Hubs namespace | Global | 6-50 | Alphanumerics and hyphens |

## Containers

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| AKS cluster | Resource group | 1-63 | Alphanumerics, underscores, hyphens. Start/end with alphanumeric. |
| AKS node pool (Linux) | Cluster | 1-12 | Lowercase letters and numbers. Start with letter. |
| AKS node pool (Windows) | Cluster | 1-6 | Lowercase letters and numbers. Start with letter. |
| Container app | Resource group | 2-32 | Lowercase, numbers, hyphens. Start with letter, end with alphanumeric. |
| Container registry | Global | 5-50 | Alphanumerics only |
| Container instance | Resource group | 1-63 | Lowercase, numbers, hyphens. No start/end/consecutive hyphens. |
| Service Fabric cluster | Region | 4-23 | Lowercase, numbers, hyphens. Start with lowercase letter, end with letter/number. |

## Databases

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Cosmos DB account | Global | 3-44 | Lowercase letters, numbers, hyphens. Start with lowercase letter or number. |
| Azure Cache for Redis | Global | 1-63 | Alphanumerics and hyphens. Start/end with alphanumeric. No consecutive hyphens. |
| SQL server | Global | 1-63 | Lowercase letters, numbers, hyphens. No start/end hyphen. |
| SQL database | Server | 1-128 | Cannot use `<>*%&:\/?` or control characters. No trailing period/space. |
| SQL Managed Instance | Global | 1-63 | Lowercase letters, numbers, hyphens. No start/end hyphen. |
| SQL Elastic Pool | Server | 1-128 | Cannot use `<>*%&:\/?` or control characters. No trailing period/space. |
| MySQL server | Global | 3-63 | Lowercase letters, numbers, hyphens. No start/end hyphen. |
| PostgreSQL server | Global | 3-63 | Lowercase letters, numbers, hyphens. No start/end hyphen. |

## Developer Tools

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| App Configuration store | Global | 5-50 | Alphanumerics and hyphens. No start/end hyphen. No consecutive double hyphens. |
| SignalR | Global | 3-63 | Alphanumerics and hyphens. Start with letter, end with letter/number. |

## Integration

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| API Management service | Global | 1-50 | Alphanumerics and hyphens. Start with letter, end with alphanumeric. |
| Logic app | Resource group | 1-43 | Alphanumerics, hyphens, underscores, periods, parentheses |
| Service Bus namespace | Global | 6-50 | Alphanumerics and hyphens. Start with letter, end with letter/number. |
| Service Bus queue | Namespace | 1-260 | Alphanumerics, periods, hyphens, underscores, slashes. Start/end with alphanumeric. |
| Service Bus topic | Namespace | 1-260 | Same as queue |

## Management and Governance

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Automation account | Resource group & region | 6-50 | Alphanumerics and hyphens. Start with letter, end with alphanumeric. |
| Application Insights | Resource group | 1-260 | Cannot use `%&\?/` or control chars. No trailing space/period. |
| Log Analytics workspace | Resource group | 4-63 | Alphanumerics and hyphens. Start/end with alphanumeric. |
| Management group | Tenant | 1-90 | Alphanumerics, hyphens, underscores, periods, parentheses. No trailing period. |
| Resource group | Subscription | 1-90 | Alphanumerics, underscores, hyphens, periods, parentheses. No trailing period. |
| Template spec | Resource group | 1-90 | Alphanumerics, underscores, parentheses, hyphens, periods |
| Purview account | Resource group | 3-63 | Alphanumerics and hyphens. Start/end with alphanumeric. |

## Migration

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Recovery Services vault | Resource group | 2-50 | Alphanumerics and hyphens. Start with letter. |

## Networking

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Virtual network | Resource group | 2-64 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric, end with alphanumeric/underscore. |
| Subnet | Virtual network | 1-80 | Same as VNet |
| Network security group | Resource group | 1-80 | Same as VNet |
| NSG security rule | NSG | 1-80 | Same as VNet |
| Public IP address | Resource group | 1-80 | Same as VNet |
| Load balancer | Resource group | 1-80 | Same as VNet |
| Application gateway | Resource group | 1-80 | Same as VNet |
| Azure Firewall | Resource group | 1-80 | Same as VNet |
| Network interface | Resource group | 1-80 | Same as VNet |
| Route table | Resource group | 1-80 | Same as VNet |
| Private endpoint | Resource group | 2-64 | Same as VNet |
| Front Door | Global | 5-64 | Alphanumerics and hyphens. Start/end with alphanumeric. |
| Front Door WAF policy | Resource group | 1-128 | Alphanumerics only. Start with letter. |
| Traffic Manager profile | Global | 1-63 | Alphanumerics and hyphens. No periods. Start/end with alphanumeric. |
| DNS zone | Resource group | 1-63 chars per label | Alphanumerics, underscores, hyphens per label. Labels separated by periods. |
| Virtual WAN | Resource group | 1-80 | Same as VNet |
| VPN Gateway | Resource group | 1-80 | Same as VNet |
| ExpressRoute circuit | Resource group | 1-80 | Same as VNet |
| NAT gateway | Resource group | 1-80 | Same as VNet |
| Bastion | Resource group | 1-80 | Same as VNet |

## Security

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Key Vault | Global | 3-24 | Alphanumerics and hyphens. Start with letter, end with letter/number. **No consecutive hyphens.** |
| Key Vault secret | Vault | 1-127 | Alphanumerics and hyphens |
| Managed identity | Resource group | 3-128 | Alphanumerics, hyphens, underscores. Start with letter/number. |

## Storage

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Storage account | Global | 3-24 | **Lowercase letters and numbers only.** No hyphens, no underscores. |
| Blob container | Storage account | 3-63 | Lowercase, numbers, hyphens. No consecutive hyphens. |
| File share | Storage account | 3-63 | Lowercase, numbers, hyphens. No start/end/consecutive hyphens. |
| Queue | Storage account | 3-63 | Lowercase, numbers, hyphens. No start/end/consecutive hyphens. |
| Table | Storage account | 3-63 | Alphanumerics. Start with letter. |
| Backup Vault | Resource group | 2-50 | Alphanumerics and hyphens. Start with letter. |

## Virtual Desktop Infrastructure

| Resource | Scope | Length | Valid Characters |
|----------|-------|--------|-----------------|
| Host pool | Resource group | 3-64 | Alphanumerics, underscores, periods, hyphens |
| Application group | Resource group | 3-64 | Same as host pool |
| Workspace | Resource group | 3-64 | Same as host pool |
