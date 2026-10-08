# Container repeatedly terminates with OOMKilled
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
