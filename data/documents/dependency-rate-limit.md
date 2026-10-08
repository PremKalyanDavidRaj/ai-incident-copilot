# External dependency returns HTTP 429
Document ID: dependency-rate-limit
Type: fictional runbook
Service: notification-worker

## Symptoms
Notification delivery slows while an external provider returns HTTP 429.
Queue backlog may rise during the same period.

## Investigation
Inspect provider status codes, Retry-After headers, and request volume.
Check retry counts and whether retries happen immediately.
Compare traffic with the provider's configured request allowance.

## Example evidence
2026-01-12T12:04:00Z provider=mail-demo status=429 retry_after_seconds=30
2026-01-12T12:04:01Z retry attempt=4 delay_ms=0
2026-01-12T12:04:05Z queue pending=840 oldest_message_seconds=120

## Interpretation
The example supports provider throttling amplified by immediate retries.
A rising queue alone does not prove rate limiting.

## Suggested response
Respect Retry-After and review bounded retries with backoff and jitter.
Verify idempotency before retrying operations with side effects.
