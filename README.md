# DataOps Pipeline Demo

Azure Function HTTP-triggered batch processor monitored by Azure SRE Agent.

## Architecture

```
Scheduled Trigger (Logic App / manual)
  └─► Azure Function HTTP: process_batch
        └─► Application Insights (telemetry)
              └─► Azure Monitor (alerts)
                    └─► Azure SRE Agent
                          └─► GitHub Issue + Copilot Fix
```

## Quick Start

```bash
# Get function key
az functionapp function keys list \
  --name dataops-pipeline-func \
  --resource-group rg-dataops-pipeline-demo \
  --function-name process_batch \
  --query "default" -o tsv

# Test
curl -X POST "https://dataops-pipeline-func.azurewebsites.net/api/pipeline/run?code=<KEY>" \
  -H "Content-Type: application/json" \
  -d '{"batch_id":"test","rows":1000,"source":"manual"}'
```

## Deployment

Infrastructure deployed via Bicep:
```bash
az deployment group create \
  --resource-group rg-dataops-pipeline-demo \
  --template-file infra/main.bicep \
  --parameters functionAppName=dataops-pipeline-func \
               appInsightsName=dataops-pipeline-insights \
               logAnalyticsName=dataops-pipeline-laws
```

Function code deployed via GitHub Releases + `WEBSITE_RUN_FROM_PACKAGE`.
