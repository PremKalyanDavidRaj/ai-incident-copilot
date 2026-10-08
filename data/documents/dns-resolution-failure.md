# Dependency hostname cannot be resolved
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
