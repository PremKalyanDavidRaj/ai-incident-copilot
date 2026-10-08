# Database connection pool exhaustion
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
