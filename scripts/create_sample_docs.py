"""Create fictional runbooks for the incident-copilot demo."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data" / "documents"

DOCUMENTS = {
    "checkout-readiness.md": """# Checkout API: 503 after deployment
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
""",
    "database-pool-exhaustion.md": """# Database connection pool exhaustion
Document ID: database-pool-exhaustion
Type: fictional runbook
Service: orders-api

## Symptoms
Requests become slow and some fail while waiting for a database connection.
The application connection pool reaches its configured limit.

## Investigation
Inspect active connections, waiting requests, query duration, and locks.
Check whether connections are returned to the pool after each request.
Compare the error start time with traffic and application changes.
Distinguish pool waiting from an inability to reach the database.

## Example evidence
2026-01-12T11:03:00Z pool active=20 idle=0 max=20 waiting=38
2026-01-12T11:03:05Z error=POOL_ACQUIRE_TIMEOUT wait_ms=30000
2026-01-12T11:03:06Z slow_query duration_ms=28000 operation=order_lookup

## Interpretation
These signals support pool exhaustion. Slow queries, locks, or leaked
connections are possible contributors; further evidence is needed.

## Suggested response
Investigate slow queries and connection handling. Do not blindly increase
pool size, because the database may already be overloaded.
""",
    "dependency-rate-limit.md": """# External dependency returns HTTP 429
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
""",
    "container-memory-limit.md": """# Container repeatedly terminates with OOMKilled
Document ID: container-memory-limit
Type: fictional runbook
Service: report-worker

## Symptoms
A worker restarts while processing large report batches.
Container status records termination reason OOMKilled.

## Investigation
Inspect the termination reason, memory usage, configured limit, and batch size.
Compare memory growth across multiple batches.
Check recent changes to buffering and in-memory data structures.

## Example evidence
2026-01-12T13:05:00Z worker batch_rows=500000 memory_mib=508 limit_mib=512
2026-01-12T13:05:03Z container termination_reason=OOMKilled exit_code=137
2026-01-12T13:05:10Z container restart_count=6

## Interpretation
The recorded OOMKilled reason supports a memory-related termination.
Exit code 137 alone does not establish an out-of-memory cause.
The evidence does not by itself distinguish a leak from a large batch.

## Suggested response
Review batch size and memory behavior. An authorized operator may adjust
resources after checking capacity; investigate recurring growth separately.
""",
    "dns-resolution-failure.md": """# Dependency hostname cannot be resolved
Document ID: dns-resolution-failure
Type: fictional runbook
Service: inventory-api

## Symptoms
Requests fail before establishing a connection to the dependency.
Logs report a hostname lookup failure.

## Investigation
Verify the configured hostname and its namespace or search domain.
Check whether resolution fails for other names in the same environment.
Inspect resolver health and recent service-name changes.
Distinguish name resolution failure from a refused TCP connection.

## Example evidence
2026-01-12T14:06:00Z dependency=stock-store.internal error=NAME_NOT_RESOLVED
2026-01-12T14:06:02Z dns query=stock-store.internal response=NXDOMAIN

## Interpretation
NXDOMAIN indicates that the queried name was reported as nonexistent.
Possible causes include a wrong hostname or missing DNS record.
This evidence does not prove the dependency process has stopped.

## Suggested response
Verify the intended service name and DNS record before changing networking.
""",
    "queue-consumer-backlog.md": """# Queue backlog with healthy downstream responses
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
""",
}


def main():
    DOCS.mkdir(parents=True, exist_ok=True)

    created = 0
    for filename, content in DOCUMENTS.items():
        path = DOCS / filename

        # Preserve any documents you have already edited.
        if path.exists():
            print(f"Kept existing: {filename}")
            continue

        path.write_text(content, encoding="utf-8")
        created += 1
        print(f"Created: {filename}")

    print(f"\nCreated {created} documents in data/documents/")


if __name__ == "__main__":
    main()
