# Queue backlog with healthy downstream responses
Document ID: queue-consumer-backlog
Type: fictional runbook
Service: event-consumer

## Symptoms
The oldest queued message becomes progressively older.
Incoming event volume exceeds the observed processing rate.

## Investigation
Compare arrival rate, processing rate, active workers, and task duration.
Check failed messages and worker restarts.
Inspect downstream responses to distinguish slow processing from throttling.

## Example evidence
2026-01-12T15:07:00Z queue arrivals_per_second=120 processed_per_second=40
2026-01-12T15:07:00Z workers active=2 task_duration_p95_ms=900
2026-01-12T15:07:05Z downstream status=200 rate_limit_errors=0
2026-01-12T15:08:00Z queue oldest_message_seconds=240

## Interpretation
The example supports a processing-capacity shortfall.
It does not show provider rate limiting.
More workers may help only if downstream capacity and task design permit.

## Suggested response
Investigate processing bottlenecks and review safe scaling options.
Preserve ordering and idempotency requirements.
