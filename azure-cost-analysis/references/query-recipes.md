# Query Recipes

Reusable cost query patterns. Each recipe shows the JSON body for `az rest --body @file.json`.

## Top 10 Most Expensive Services (Current Month)

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "ServiceName" }]
  }
}
```

## Cost by Resource Group

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "ResourceGroupName" }]
  }
}
```

## Daily Cost for a Specific Resource

Replace `<full-resource-id>` with the output of `az resource list --name <name> --query "[0].id" -o tsv`.

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "Daily",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [
      { "type": "Dimension", "name": "Meter" },
      { "type": "Dimension", "name": "MeterCategory" }
    ],
    "filter": {
      "dimensions": {
        "name": "ResourceId",
        "operator": "In",
        "values": ["<full-resource-id>"]
      }
    }
  }
}
```

## Cost by Meter within a Resource Group

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [
      { "type": "Dimension", "name": "Meter" },
      { "type": "Dimension", "name": "MeterCategory" }
    ],
    "filter": {
      "dimensions": {
        "name": "ResourceGroupName",
        "operator": "In",
        "values": ["<resource-group-name>"]
      }
    }
  }
}
```

## Month-over-Month Comparison (Last Month)

```json
{
  "type": "ActualCost",
  "timeframe": "TheLastMonth",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "ServiceName" }]
  }
}
```

## Custom Date Range with Service Breakdown

```json
{
  "type": "ActualCost",
  "timeframe": "Custom",
  "timePeriod": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "dataset": {
    "granularity": "Daily",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "ServiceName" }]
  }
}
```

## Amortized Cost (Reservations Spread Over Term)

```json
{
  "type": "AmortizedCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [
      { "type": "Dimension", "name": "ServiceName" },
      { "type": "Dimension", "name": "PricingModel" }
    ]
  }
}
```

## Filter by Multiple Resource Groups

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "None",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "ServiceName" }],
    "filter": {
      "dimensions": {
        "name": "ResourceGroupName",
        "operator": "In",
        "values": ["rg-prod", "rg-staging"]
      }
    }
  }
}
```

## Compound Filter (Resource Group + Service)

```json
{
  "type": "ActualCost",
  "timeframe": "MonthToDate",
  "dataset": {
    "granularity": "Daily",
    "aggregation": { "totalCost": { "name": "Cost", "function": "Sum" } },
    "grouping": [{ "type": "Dimension", "name": "Meter" }],
    "filter": {
      "and": [
        { "dimensions": { "name": "ResourceGroupName", "operator": "In", "values": ["my-rg"] } },
        { "dimensions": { "name": "MeterCategory", "operator": "In", "values": ["Virtual Machines"] } }
      ]
    }
  }
}
```
