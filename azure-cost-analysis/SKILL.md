---
name: azure-cost-analysis
description: Analyze Azure service costs using the Microsoft.CostManagement REST API via az rest. Use when investigating Azure spending, querying cost breakdowns by resource, meter, or service, identifying cost anomalies, or providing cost reduction recommendations. Covers query construction, valid dimensions and filters, daily and monthly granularity, and common pitfalls. Triggers on Azure cost, Azure spending, Azure billing, cost analysis, cost breakdown, cost optimization, expensive resource, cost management query.
---

# Azure Cost Analysis via Cost Management REST API

Query Azure costs programmatically using the `Microsoft.CostManagement/query` REST API through `az rest`.

## Why `az rest` Instead of `az costmanagement`

The `costmanagement` CLI extension (v1.0.0) only exposes `export` and `show-operation-result` — no `query` subcommand. Use `az rest` to call the REST API directly.

## Workflow

1. Identify the target resource (name, resource group, full resource ID)
2. Build a cost query JSON body
3. Execute via `az rest`
4. Parse and analyze results

## API Endpoint

```
POST https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query?api-version=2023-11-01
```

Scoping options:
- **Subscription**: `/subscriptions/{id}/providers/Microsoft.CostManagement/query`
- **Resource group**: `/subscriptions/{id}/resourceGroups/{rg}/providers/Microsoft.CostManagement/query`

## Query Body Structure

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "Daily",
    "aggregation": {
      "totalCost": { "name": "Cost", "function": "Sum" }
    },
    "grouping": [
      { "type": "Dimension", "name": "<DimensionName>" }
    ],
    "filter": {
      "dimensions": {
        "name": "<DimensionName>",
        "operator": "In",
        "values": ["<value>"]
      }
    }
  }
}
```

### Key Parameters

| Field | Options |
|-------|---------|
| `type` | `ActualCost`, `AmortizedCost` |
| `timeframe` | `MonthToDate`, `BillingMonthToDate`, `TheLastMonth`, `TheLastBillingMonth`, `WeekToDate`, `Custom` |
| `granularity` | `None`, `Daily`, `Monthly` |

For `Custom` timeframe, add `timePeriod`:
```json
"timeframe": "Custom",
"timePeriod": { "from": "2026-01-01T00:00:00Z", "to": "2026-01-31T23:59:59Z" }
```

## Valid Dimensions

For grouping and filtering — use **only** these values:

`ResourceGroup`, `ResourceGroupName`, `ResourceType`, `ResourceId`, `ResourceLocation`, `SubscriptionId`, `SubscriptionName`, `MeterCategory`, `MeterSubcategory`, `Meter`, `ServiceFamily`, `ServiceName`, `UnitOfMeasure`, `ChargeType`, `PublisherType`, `PricingModel`, `Frequency`, `BillingMonth`, `ReservationId`, `ReservationName`, `Product`, `PartNumber`, `ResourceGuid`, `BenefitId`, `BenefitName`, `Provider`, `InvoiceId`, `CostAllocationRuleName`

**Common pitfall**: `MeterName` is **invalid** — use `Meter` instead.

## Filter Constraints

- `ResourceId` only supports the **`In`** operator (not `Contains`). Provide the **full resource ID**.
- Other dimensions support `In` as well.
- Combine filters with `and`/`or`/`not`:

```json
"filter": {
  "and": [
    { "dimensions": { "name": "ResourceGroupName", "operator": "In", "values": ["my-rg"] } },
    { "dimensions": { "name": "MeterCategory", "operator": "In", "values": ["Virtual Machines"] } }
  ]
}
```

## Discovering the Full Resource ID

```bash
az resource list --name <resource-name> --query "[0].id" -o tsv
```

Or filter by type:
```bash
az resource list --resource-type "Microsoft.Compute/virtualMachines" --query "[].{name:name, id:id}" -o table
```

## Execution

Always write the query body to a file first (avoids shell escaping issues):

```bash
python3 -c '
import json
query = { ... }  # build query dict
with open("/tmp/cost_query.json", "w") as f:
    json.dump(query, f)
'
```

Then execute:
```bash
az rest --method post \
  --url "https://management.azure.com/subscriptions/{sub-id}/providers/Microsoft.CostManagement/query?api-version=2023-11-01" \
  --headers "Content-Type=application/json" \
  --body @/tmp/cost_query.json \
  -o json > /tmp/cost_result.json
```

**Important**: Always include `--headers "Content-Type=application/json"` when using `--body @file` to avoid `415 Unsupported Media Type` errors.

## Parsing Results

Response structure:
```json
{
  "properties": {
    "columns": [ { "name": "Cost", "type": "Number" }, ... ],
    "rows": [ [10.56, 20260201, "VM", "Virtual Machines", "USD"], ... ],
    "nextLink": null
  }
}
```

Parse with Python:
```python
import json
with open("/tmp/cost_result.json") as f:
    data = json.load(f)
rows = data["properties"]["rows"]
cols = [c["name"] for c in data["properties"]["columns"]]
for r in sorted(rows, key=lambda x: float(x[0]), reverse=True)[:10]:
    print(f"${float(r[0]):.2f} — {r[1:]}")
```

Handle pagination if `nextLink` is not null by making a GET request to that URL.

## Common Query Recipes

For specific resource, service, or subscription-level queries, see [references/query-recipes.md](references/query-recipes.md).

## Cost Reduction Analysis

After querying costs, apply these analysis steps:

1. **Identify top cost drivers** — group by `ServiceName` or `MeterCategory` at subscription scope
2. **Drill into specific resources** — filter by `ResourceId` with `Daily` granularity to spot trends
3. **Detect idle resources** — look for flat daily costs with no active usage (always-on charges)
4. **Compare periods** — run `TheLastMonth` vs `MonthToDate` to find spikes
5. **Check meter details** — group by `Meter` + `MeterCategory` to understand what exactly is being charged
