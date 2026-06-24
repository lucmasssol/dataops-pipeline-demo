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
               logAnalyticsName=dataops-pipeline-laws \
               packageUrl=https://github.com/lucmasssol/dataops-pipeline-demo/releases/download/v1.0.2/function-v1.0.2.zip
```

Function code deployed via GitHub Releases + `WEBSITE_RUN_FROM_PACKAGE`.

## Release Process

Releases are created automatically by the [Release workflow](.github/workflows/release.yml)
when a version tag is pushed:

```bash
git tag v1.0.2
git push origin v1.0.2
```

The workflow will:
1. Package `src/function_http/` into a zip archive.
2. **Validate** the package — any `RuntimeError` raise or `rows > N` threshold check
   in `process_batch/__init__.py` will block the release (post-incident control
   introduced after the [v1.0.1 incident](https://github.com/lucmasssol/dataops-pipeline-demo/issues/3)).
3. Publish a GitHub Release with the validated zip attached.

To promote a release to production, redeploy the Bicep template with the new `packageUrl`
(see Deployment section above) or update the `WEBSITE_RUN_FROM_PACKAGE` app setting directly.

## Incident History

| Version | Status | Notes |
|---------|--------|-------|
| v1.0.0 | ✅ Good | Initial stable release |
| v1.0.1 | ❌ Bad | Contained `RuntimeError: memory pressure detected on large batch` guard (rows > 50000); caused production failures on 2026-06-24 |
| v1.0.2 | ✅ Good | Known-good release from `main`; validated by automated release gate |

