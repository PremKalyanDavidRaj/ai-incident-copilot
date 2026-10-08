# Checkout API: 503 after deployment
Document ID: checkout-readiness
Type: fictional runbook
Service: checkout-api

## Symptoms
Customers receive HTTP 503 immediately after a deployment.
Application processes may be running while readiness checks fail.

## Investigation
Compare the deployment time with the first 503 response.
Inspect readiness failures and whether the service has ready endpoints.
Compare the configured readiness path with the application's health route.
Check startup logs before assuming the database is unavailable.

## Example evidence
2026-01-12T10:02:00Z deployment version=v2.4.0 service=checkout-api
2026-01-12T10:02:12Z readiness probe path=/ready status=404
2026-01-12T10:02:15Z gateway upstream=checkout-api ready_endpoints=0 status=503

## Interpretation
In this example, a readiness-path mismatch prevents traffic routing.
A 503 alone does not establish this cause.

## Suggested response
Have an authorized operator correct the readiness path or consider rollback
after reviewing the deployment. Verify readiness and successful requests.
The copilot must not execute changes.
