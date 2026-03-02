# Azure Resource Naming Rules and Restrictions

Full naming rules and character constraints per the [Azure Resource Manager documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules).

> **Note:** Resource and resource group names are case-insensitive unless specifically noted. The term *alphanumeric* refers to `a-z`, `A-Z`, and `0-9`. Resources with a public endpoint can't include reserved words or trademarks. Don't use `#` in a resource name — it interferes with URL parsing.

## Contents

- [Microsoft.AnalysisServices](#microsoftanalysisservices)
- [Microsoft.ApiManagement](#microsoftapimanagement)
- [Microsoft.App](#microsoftapp)
- [Microsoft.AppConfiguration](#microsoftappconfiguration)
- [Microsoft.Automation](#microsoftautomation)
- [Microsoft.Batch](#microsoftbatch)
- [Microsoft.Cache](#microsoftcache)
- [Microsoft.Cdn](#microsoftcdn)
- [Microsoft.CognitiveServices](#microsoftcognitiveservices)
- [Microsoft.Compute](#microsoftcompute)
- [Microsoft.ContainerInstance](#microsoftcontainerinstance)
- [Microsoft.ContainerRegistry](#microsoftcontainerregistry)
- [Microsoft.ContainerService](#microsoftcontainerservice)
- [Microsoft.DataFactory](#microsoftdatafactory)
- [Microsoft.DataLakeStore](#microsoftdatalakestore)
- [Microsoft.DataProtection](#microsoftdataprotection)
- [Microsoft.DBforMySQL](#microsoftdbformysql)
- [Microsoft.DBforPostgreSQL](#microsoftdbforpostgresql)
- [Microsoft.Devices](#microsoftdevices)
- [Microsoft.DocumentDB](#microsoftdocumentdb)
- [Microsoft.EventGrid](#microsofteventgrid)
- [Microsoft.EventHub](#microsofteventhub)
- [Microsoft.Insights](#microsoftinsights)
- [Microsoft.KeyVault](#microsoftkeyvault)
- [Microsoft.Kusto](#microsoftkusto)
- [Microsoft.Logic](#microsoftlogic)
- [Microsoft.MachineLearningServices](#microsoftmachinelearningservices)
- [Microsoft.ManagedIdentity](#microsoftmanagedidentity)
- [Microsoft.Management](#microsoftmanagement)
- [Microsoft.Network](#microsoftnetwork)
- [Microsoft.NotificationHubs](#microsoftnotificationhubs)
- [Microsoft.OperationalInsights](#microsoftoperationalinsights)
- [Microsoft.RecoveryServices](#microsoftrecoveryservices)
- [Microsoft.Resources](#microsoftresources)
- [Microsoft.Search](#microsoftsearch)
- [Microsoft.ServiceBus](#microsoftservicebus)
- [Microsoft.ServiceFabric](#microsoftservicefabric)
- [Microsoft.SignalRService](#microsoftsignalrservice)
- [Microsoft.Sql](#microsoftsql)
- [Microsoft.Storage](#microsoftstorage)
- [Microsoft.Synapse](#microsoftsynapse)
- [Microsoft.Web](#microsoftweb)
- [Microsoft.DesktopVirtualization](#microsoftdesktopvirtualization)

## Full Rules by Resource Provider

### Microsoft.AnalysisServices

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| servers | Resource group | 3-63 | Lowercase letters and numbers. Start with lowercase letter. |

### Microsoft.ApiManagement

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| service | Global | 1-50 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| service / apis | Service | 1-80 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| service / products | Service | 1-80 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| service / subscriptions | Service | 1-80 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| service / users | Service | 1-80 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |

### Microsoft.App

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| containerApps | Resource group | 2-32 | Lowercase letters, numbers, hyphens. Start with letter; end with alphanumeric. |

### Microsoft.AppConfiguration

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| configurationStores | Global | 5-50 | Alphanumerics and hyphens. Can't contain more than 2 consecutive hyphens. Can't start/end with hyphen. |

### Microsoft.Automation

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| automationAccounts | Resource group & region | 6-50 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| automationAccounts / runbooks | Automation account | 1-63 | Alphanumerics, underscores, hyphens. Start with letter. |

### Microsoft.Batch

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| batchAccounts | Region | 3-24 | Lowercase letters and numbers. |
| batchAccounts / pools | Batch account | 1-64 | Alphanumerics, underscores, hyphens. |

### Microsoft.Cache

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| Redis | Global | 1-63 | Alphanumerics and hyphens. Start and end with alphanumeric. No consecutive hyphens. |

### Microsoft.Cdn

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| profiles | Resource group | 1-260 | Alphanumerics and hyphens. Start and end with alphanumeric. |
| profiles / endpoints | Global | 1-50 | Alphanumerics and hyphens. Start and end with alphanumeric. |

### Microsoft.CognitiveServices

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| accounts | Resource group | 2-64 | Alphanumerics and hyphens. Start and end with alphanumeric. |

### Microsoft.Compute

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| availabilitySets | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| disks | Resource group | 1-80 | Alphanumerics, underscores, hyphens. |
| galleries | Resource group | 1-80 | Alphanumerics and periods. Start and end with alphanumeric. |
| snapshots | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| virtualMachines | Resource group | 1-15 (Windows) / 1-64 (Linux) | Can't use spaces, control chars, or `~ ! @ # $ % ^ & * ( ) = + _ [ ] { } \ | ; : . ' " , < > / ?`. Windows: no periods, can't end with hyphen. Linux: can't end with period/hyphen. |
| virtualMachineScaleSets | Resource group | 1-15 (Windows) / 1-64 (Linux) | Same as VMs. Can't start with underscore. Can't end with period/hyphen. |

> **Note:** Azure VMs have two names: resource name (up to 64 chars) and host name (limits above). The portal uses the same value for both.

### Microsoft.ContainerInstance

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| containerGroups | Resource group | 1-63 | Lowercase letters, numbers, hyphens. Can't start/end with hyphen. No consecutive hyphens. |

### Microsoft.ContainerRegistry

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| registries | Global | 5-50 | Alphanumerics only. |
| registries / webhooks | Registry | 5-50 | Alphanumerics only. |

### Microsoft.ContainerService

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| managedClusters | Resource group | 1-63 | Alphanumerics, underscores, hyphens. Start and end with alphanumeric. |
| managedClusters / agentPools | Managed cluster | 1-12 (Linux) / 1-6 (Windows) | Lowercase letters and numbers. Can't start with a number. |

### Microsoft.DataFactory

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| factories | Global | 3-63 | Alphanumerics and hyphens. Start and end with alphanumeric. |
| factories / pipelines | Factory | 1-260 | Can't use `<>*#.%&:\+?/` or control chars. Start with alphanumeric. |

### Microsoft.DataLakeStore

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| accounts | Global | 3-24 | Lowercase letters and numbers. |

### Microsoft.DataProtection

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| backupVaults | Resource group | 2-50 | Alphanumerics and hyphens. Start with letter. |

### Microsoft.DBforMySQL

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| servers | Global | 3-63 | Lowercase letters, hyphens, numbers. Can't start/end with hyphen. |

### Microsoft.DBforPostgreSQL

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| servers | Global | 3-63 | Lowercase letters, hyphens, numbers. Can't start/end with hyphen. |

### Microsoft.Devices

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| IotHubs | Global | 3-50 | Alphanumerics and hyphens. Can't end with hyphen. |
| provisioningServices | Resource group | 3-64 | Alphanumerics and hyphens. End with alphanumeric. |

### Microsoft.DocumentDB

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| databaseAccounts | Global | 3-44 | Lowercase letters, numbers, hyphens. Start with lowercase letter or number. |

### Microsoft.EventGrid

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| domains | Resource group | 3-50 | Alphanumerics and hyphens. |
| topics | Region | 3-50 | Alphanumerics and hyphens. |
| eventSubscriptions | Resource group | 3-64 | Alphanumerics and hyphens. |

### Microsoft.EventHub

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| namespaces | Global | 6-50 | Alphanumerics and hyphens. Start with letter; end with letter/number. |
| namespaces / eventhubs | Namespace | 1-256 | Alphanumerics, periods, hyphens, underscores. Start and end with letter/number. |
| namespaces / consumergroups | Event hub | 1-50 | Alphanumerics, periods, hyphens, underscores. Start and end with letter/number. |

### Microsoft.Insights

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| components (Application Insights) | Resource group | 1-260 | Can't use `%&\?/` or control chars. Can't end with space or period. |
| actionGroups | Resource group | 1-260 | Can't use `:<>+/&%\?|` or control chars. Can't end with space or period. |

### Microsoft.KeyVault

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| vaults | Global | 3-24 | Alphanumerics and hyphens. Start with letter; end with letter/number. No consecutive hyphens. |
| vaults / secrets | Vault | 1-127 | Alphanumerics and hyphens. |

### Microsoft.Kusto

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| clusters | Global | 4-22 | Lowercase letters and numbers. Start with letter. |
| clusters / databases | Cluster | 1-260 | Alphanumerics, hyphens, spaces, periods. |

### Microsoft.Logic

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| workflows | Resource group | 1-43 | Alphanumerics, hyphens, underscores, periods, parentheses. |
| integrationAccounts | Resource group | 1-80 | Alphanumerics, hyphens, underscores, periods, parentheses. |

### Microsoft.MachineLearningServices

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| workspaces | Resource group | 3-33 | Alphanumerics, hyphens, underscores. |
| workspaces / computes | Workspace | 3-24 (compute instance) / 3-32 (AML compute) | Alphanumerics and hyphens. |

### Microsoft.ManagedIdentity

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| userAssignedIdentities | Resource group | 3-128 | Alphanumerics, hyphens, underscores. Start with letter or number. |

### Microsoft.Management

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| managementGroups | Tenant | 1-90 | Alphanumerics, hyphens, underscores, periods, parentheses. Start with letter/number. Can't end with period. |

### Microsoft.Network

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| applicationGateways | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| azureFirewalls | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| bastionHosts | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| connections | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| dnsZones | Resource group | 1-63 chars, 2-34 labels | Each label: alphanumerics, underscores, hyphens. Labels separated by periods. |
| expressRouteCircuits | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| frontDoors | Global | 5-64 | Alphanumerics and hyphens. Start and end with alphanumeric. |
| loadBalancers | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| localNetworkGateways | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| natGateways | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric. |
| networkInterfaces | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| networkSecurityGroups | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| privateDnsZones | Resource group | 1-63 chars, 2-34 labels | Each label: alphanumerics, underscores, hyphens. Labels separated by periods. |
| privateEndpoints | Resource group | 2-64 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| publicIPAddresses | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| routeTables | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| trafficManagerProfiles | Global | 1-63 | Alphanumerics and hyphens. Start and end with alphanumeric. No periods in profile name. |
| virtualNetworkGateways | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| virtualNetworks | Resource group | 2-64 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| virtualNetworks / subnets | VNet | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| virtualNetworks / virtualNetworkPeerings | VNet | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| virtualWans | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |
| vpnGateways | Resource group | 1-80 | Alphanumerics, underscores, periods, hyphens. Start with alphanumeric; end with alphanumeric/underscore. |

### Microsoft.NotificationHubs

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| namespaces | Global | 6-50 | Alphanumerics and hyphens. Start with letter; end with alphanumeric. |
| namespaces / notificationHubs | Namespace | 1-260 | Alphanumerics, periods, hyphens, underscores. Start with alphanumeric. |

### Microsoft.OperationalInsights

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| workspaces | Resource group | 4-63 | Alphanumerics and hyphens. Start and end with alphanumeric. |

### Microsoft.RecoveryServices

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| vaults | Resource group | 2-50 | Alphanumerics and hyphens. Start with letter. |

### Microsoft.Resources

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| resourceGroups | Subscription | 1-90 | Alphanumerics, underscores, hyphens, periods, parentheses. Can't end with period. |
| deployments | Resource group | 1-64 | Alphanumerics, underscores, parentheses, hyphens, periods. |
| templateSpecs | Resource group | 1-90 | Alphanumerics, underscores, parentheses, hyphens, periods. |

### Microsoft.Search

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| searchServices | Global | 2-60 | Alphanumerics and hyphens. Can't use hyphens as first two or last chars. No consecutive hyphens. |

### Microsoft.ServiceBus

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| namespaces | Global | 6-50 | Alphanumerics and hyphens. Start with letter; end with letter/number. |
| namespaces / queues | Namespace | 1-260 | Alphanumerics, periods, hyphens, underscores, slashes. Start and end with alphanumeric. |
| namespaces / topics | Namespace | 1-260 | Alphanumerics, periods, hyphens, underscores, slashes. Start and end with alphanumeric. |
| namespaces / topics / subscriptions | Topic | 1-50 | Alphanumerics, periods, hyphens, underscores. Start and end with alphanumeric. |

### Microsoft.ServiceFabric

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| clusters | Region | 4-23 | Lowercase letters, numbers, hyphens. Start with lowercase letter; end with lowercase letter/number. |

### Microsoft.SignalRService

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| signalR | Global | 3-63 | Alphanumerics and hyphens. Start with letter; end with letter/number. |

### Microsoft.Sql

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| servers | Global | 1-63 | Lowercase letters, numbers, hyphens. Can't start/end with hyphen. |
| servers / databases | Server | 1-128 | Can't use `<>*%&:\/?` or control chars. Can't end with period or space. |
| servers / elasticPools | Server | 1-128 | Can't use `<>*%&:\/?` or control chars. Can't end with period or space. |
| managedInstances | Global | 1-63 | Lowercase letters, numbers, hyphens. Can't start/end with hyphen. |

### Microsoft.Storage

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| storageAccounts | Global | 3-24 | Lowercase letters and numbers only. |
| storageAccounts / blobServices / containers | Storage account | 3-63 | Lowercase letters, numbers, hyphens. Start with lowercase letter/number. No consecutive hyphens. |
| storageAccounts / fileServices / shares | Storage account | 3-63 | Lowercase letters, numbers, hyphens. Can't start/end with hyphen. No consecutive hyphens. |
| storageAccounts / queues | Storage account | 3-63 | Lowercase letters, numbers, hyphens. Can't start/end with hyphen. No consecutive hyphens. |
| storageAccounts / tables | Storage account | 3-63 | Alphanumerics. Start with letter. |

### Microsoft.Synapse

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| workspaces | Global | 1-50 | Lowercase letters, hyphens, numbers. Start and end with letter/number. Can't contain `-ondemand`. |
| workspaces / bigDataPools | Workspace | 1-15 | Letters and numbers. Start with letter; end with letter/number. |
| workspaces / sqlPools | Workspace | 1-60 | Can't contain `<>*%&:\/?@-` or control chars. Can't end with period or space. |

### Microsoft.Web

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| serverfarms (App Service plan) | Resource group | 1-60 | Alphanumerics, hyphens, Unicode (Punycode). |
| sites (Web app / Function app) | Global (or per domain for ASE) | 2-60 | Alphanumerics, hyphens, Unicode (Punycode). Can't start/end with hyphen. |
| sites / slots | Site | 2-59 | Alphanumerics, hyphens, Unicode (Punycode). |

> **Note:** Web apps must have a globally unique URL (`http://<app-name>.azurewebsites.net`). Azure Functions follows the same rules; function app names are truncated to 32 characters for host ID generation.

### Microsoft.DesktopVirtualization

| Entity | Scope | Length | Valid Characters |
|--------|-------|--------|-----------------|
| hostPools | Resource group | 3-64 | Alphanumerics, underscores, periods, hyphens. Start with letter/number; end with letter/number/underscore. |
| applicationGroups | Resource group | 3-64 | Alphanumerics, underscores, periods, hyphens. Start with letter/number; end with letter/number/underscore. |
| workspaces | Resource group | 3-64 | Alphanumerics, underscores, periods, hyphens. Start with letter/number; end with letter/number/underscore. |
