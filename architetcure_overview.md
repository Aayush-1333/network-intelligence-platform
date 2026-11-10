# Telecom Network Intelligence Platform

## Architecture and Design Specification

**Document purpose:** Define the target architecture, technology stack, data flows, agent design, security controls, operational guardrails, and staged delivery approach for a multi-tenant Telecom Network Intelligence Platform on Google Cloud.

---

## 1. Executive Summary

The Telecom Network Intelligence Platform provides trusted, low-latency network insights to operational users and role-based AI agents. It combines three core data capabilities with a governed agent execution layer:

1. **Connection Factory** — ingests, validates, normalizes, and routes inventory, performance, and alarm data from vendor and operational systems.
2. **KPI Engine** — stores and processes high-volume performance measurements and exposes curated, time-aligned KPI data.
3. **Topology Engine** — maintains a time-aware representation of network entities and their relationships, supporting bounded topology traversal and historical reconstruction.
4. **Agent Layer** — runs role-specific AI agents that investigate alarms, analyze performance, and propose network changes using controlled APIs and Model Context Protocol (MCP) tools.

The target platform is designed for an initial operating envelope of five customers, approximately 250,000 cells, two million topology relationships, and approximately 50 million telemetry rows per day, with performance-counter data arriving in 15-minute bursts. These figures are planning inputs and must be validated through load, latency, and cost testing.

### 1.1 Target architecture decisions

| Capability | Target technology | Architectural role |
| :--- | :--- | :--- |
| Ingestion and event backbone | Cloud Run Jobs, Cloud Run services, Pub/Sub, and Cloud Storage | Batch, event-driven, and file-based ingestion |
| Topology persistence | Cloud SQL for PostgreSQL | Tenant-scoped entities, relationships, and bitemporal topology facts |
| Topology acceleration | Memorystore for Redis | Versioned cache of frequently requested, bounded topology subgraphs |
| KPI persistence and analytics | BigQuery | High-volume time-series storage, aggregation, and analytical queries |
| Agent framework | Google Agent Development Kit (ADK) for Python | Agent definitions, orchestration, tool use, and evaluation |
| Foundation model | Gemini through Vertex AI | Language reasoning and structured agent responses |
| API and MCP services | Python, FastAPI, MCP Python SDK | Authenticated API and tool interfaces |
| Agent and API runtime | Cloud Run services | Request-driven agent and tool services |
| Asynchronous processing | Pub/Sub with Cloud Run worker pools and Cloud Run Jobs | Event consumers, background work, and finite batch tasks |
| Secrets and identity | IAM, service accounts, Secret Manager, OAuth 2.0 / OIDC | Workload identity, user authentication, and secret management |
| Build and release | Cloud Build, Artifact Registry | Container build, scanning/integration gates, and deployment pipeline |
| Operations | Cloud Logging, Cloud Monitoring, Cloud Trace, Error Reporting | Logs, metrics, traces, and failure diagnosis |

**Topology database decision:** Cloud SQL for PostgreSQL is the baseline persistence layer. A dedicated graph database or Spanner Graph is not a default requirement for the stated initial scale. Reconsider a graph-specific platform only if measured traversal latency, concurrency, relationship growth, operational complexity, or availability requirements justify the additional cost and migration effort.

**Agent framework decision:** Use Google ADK for Python with Gemini models accessed through Vertex AI. Implement the API and MCP tool services with FastAPI and the MCP Python SDK. This provides a coherent Google Cloud deployment path while keeping agent logic, tools, and evaluation code in Python.

---

## 2. Scope, Scale, and Service Objectives

### 2.1 Initial planning envelope

| Dimension | Planning value |
| :--- | :--- |
| Customers / tenants | 5 |
| Network cells | Approximately 250,000 |
| Topology relationships | Approximately 2 million |
| Performance telemetry | Approximately 50 million rows per day |
| Performance measurement interval | 15 minutes |
| Late-arriving performance data | Up to 2 hours |
| Typical topology request | Bounded two-hop traversal |
| Topology latency objective | Less than 2 seconds at p95 for two-hop lookups |
| Agent concurrency scenario | 100 concurrent agent workloads |
| Tool execution timeout | 25 seconds |
| End-to-end agent response target | 30 seconds |
| Maximum topology traversal depth | 3 hops |

These values are design targets, not demonstrated production capacity. They must be verified with representative tenant distributions, data skew, query patterns, and concurrent workloads.

### 2.2 Service objectives and operating principles

- Keep interactive agent requests separate from bulk ingestion, historical recalculation, and large analytical workloads.
- Apply tenant scope and authorization at every service boundary, not only at the user-facing API.
- Bound topology traversal, KPI query windows, tool execution time, and agent iteration count.
- Return data quality, provenance, and completeness metadata with evidence.
- Prefer deterministic preprocessing and typed tool responses over unconstrained agent access to source systems.
- Require human approval for production-impacting network changes.
- Treat confidence as an evidence-quality indicator, not as a substitute for explicit data-quality and safety rules.

---

## 3. Logical Architecture and End-to-End Data Flow

```text
                    ┌─────────────────────────────┐
                    │ Vendor / OSS / BSS Sources  │
                    │ SFTP, APIs, streams, alarms │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │ Connection Factory          │
                    │ Cloud Run Jobs / Services   │
                    │ Validation and normalization│
                    └──────────────┬──────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
                         ▼                   ▼
              ┌──────────────────┐  ┌────────────────────┐
              │ Pub/Sub          │  │ Cloud Storage      │
              │ Event backbone   │  │ Raw landing/staging│
              └────────┬─────────┘  └──────────┬─────────┘
                       │                       │
             ┌─────────┴──────────┐            │
             │                    │            │
             ▼                    ▼            ▼
  ┌────────────────────┐  ┌─────────────────────────────┐
  │ Topology processing│  │ KPI processing              │
  │ Cloud Run services │  │ Cloud Run workers / Jobs    │
  └─────────┬──────────┘  └──────────────┬──────────────┘
            │                            │
            ▼                            ▼
  ┌────────────────────┐       ┌────────────────────────┐
  │ Cloud SQL           │       │ BigQuery               │
  │ PostgreSQL          │       │ Raw, curated, rollups  │
  └─────────┬──────────┘       └────────────┬───────────┘
            │                               │
            ▼                               ▼
  ┌────────────────────┐       ┌────────────────────────┐
  │ Memorystore Redis  │       │ KPI query / MCP service│
  │ Topology cache     │       └────────────┬───────────┘
  └─────────┬──────────┘                    │
            │                               │
            └──────────────┬────────────────┘
                           ▼
                ┌───────────────────────────┐
                │ Private MCP Tool Plane    │
                │ Topology / KPI / Alarm    │
                │ and Change Proposal tools │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ Agent Access Gateway      │
                │ FastAPI on Cloud Run      │
                │ OIDC/JWT and tenant scope │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ Agent Runtime             │
                │ Python Google ADK         │
                │ Gemini on Vertex AI       │
                │ Specialist role agents    │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ User response / proposed  │
                │ change ticket             │
                │ Human approval for writes │
                └───────────────────────────┘
```

### 3.1 Connection Factory — ingestion and normalization

The Connection Factory is responsible for receiving source data, validating its structure, normalizing vendor-specific representations, and publishing canonical records or processing events.

**Runtime and components**

- Use **Cloud Run Jobs** for finite, scheduled tasks such as hourly inventory imports and reconciliation.
- Use **Cloud Run services** for request-driven ingestion endpoints and adapters that must remain available to receive callbacks or API pushes.
- Use **Pub/Sub** to decouple source ingestion from downstream topology and KPI processing.
- Use **Cloud Storage** as the landing and raw-staging location for file-based feeds and replayable source payloads.
- Use tenant-aware schemas and validation rules to prevent vendor-specific formats from leaking into downstream services.

**Processing responsibilities**

1. Authenticate the source or ingestion client.
2. Identify the tenant and source system.
3. Validate schema, required identifiers, timestamps, and payload integrity.
4. Normalize vendor-specific fields into canonical platform entities and measurements.
5. Apply idempotency and duplicate detection.
6. Persist raw source material where replay and auditability are required.
7. Publish normalized events to Pub/Sub for downstream processing.
8. Route invalid or unresolved records to quarantine with actionable error metadata.

Inventory imports are expected hourly. Performance counters are expected in 15-minute measurement intervals, with approximately 50 million rows per day in the stated planning scenario.

### 3.2 Synchronous, event-driven, and batch execution

| Processing mode | Appropriate workloads | Runtime |
| :--- | :--- | :--- |
| Synchronous | User-facing API requests, MCP tool calls, bounded topology reads, KPI evidence retrieval | Cloud Run services |
| Event-driven | File arrival, ingestion completion, alarm generation, topology-change notification, cache invalidation | Pub/Sub and Cloud Run services / worker pools |
| Batch | Hourly inventory reconciliation, scheduled late-data repair, formula recalculation, daily rollups | Cloud Run Jobs and workflows |

Interactive request paths must not wait for large historical recalculations or full inventory reconciliation.

---

## 4. Topology Engine and Inventory Model

### 4.1 Persistence model

Use **Cloud SQL for PostgreSQL** as the initial topology system of record. Model network entities and relationships using tenant-scoped relational tables, indexed adjacency access paths, and bounded recursive common table expressions (CTEs).

A representative logical model includes:

- `tenant` — customer or tenant identity.
- `network_entity` — immutable entity identifier, entity type, tenant identifier, and lifecycle metadata.
- `topology_relationship` — source entity, target entity, relationship type, tenant identifier, and validity interval.
- `topology_version` — version or snapshot metadata for a coherent topology state.
- `source_observation` — source system, source timestamp, ingestion timestamp, and source priority.
- `unresolved_entity` — unresolved or incomplete entity references awaiting reconciliation.

Use immutable entity UUIDs as stable references. Vendor identifiers, names, and external identifiers should be stored as attributes or mappings rather than used as the only permanent identity.

### 4.2 Bounded traversal and indexing

- Enforce a maximum traversal depth of three hops at the API and repository layers.
- Optimize the common two-hop lookup using tenant-scoped indexes on relationship source, target, type, and validity fields.
- Apply tenant filtering inside the query, not only after the result is returned.
- Set row limits and query timeouts to prevent unexpectedly large graph expansions.
- Return the topology version and effective timestamp used to construct the result.
- Use query plans and representative data distributions to validate index selection and traversal performance.

PostgreSQL recursive CTEs are suitable for the initial bounded traversal pattern. A dedicated graph engine should be considered only after benchmark evidence shows that the relational design cannot meet the required service objectives at acceptable cost and operational complexity.

### 4.3 Topology cache

Use **Memorystore for Redis** to cache frequently requested, bounded topology subgraphs.

Cache design:

- Include tenant identity, root entity, traversal depth, topology version, and relevant query options in the cache key.
- Cache only bounded results, such as commonly requested one-hop and two-hop neighborhoods.
- Invalidate or version-bump affected cache entries when topology changes are committed.
- Use a time-to-live (TTL) as a fallback against stale entries if an invalidation event is missed.
- Coalesce identical concurrent cache misses where practical.
- Apply per-tenant rate limits and cache admission controls to protect Redis from high-cardinality or abusive query patterns.
- Do not treat a cache entry as authoritative when its topology version is inconsistent with the requested effective time.

### 4.4 Missing, duplicated, and conflicting inventory records

**Deduplication**

- Use idempotent ingestion based on tenant, source system, vendor identifiers, and stable entity identifiers.
- Where source payloads can be repeated or revised, calculate a deterministic payload hash to identify duplicate deliveries.
- Distinguish duplicate delivery from a legitimate source correction.

**Missing and unresolved records**

- Preserve the raw record and its validation failure in a quarantine or staging area.
- Create a provisional unresolved entity reference (sometimes called a "ghost node") only where it is necessary to preserve relationship context for downstream correlation.
- Mark provisional entities explicitly, for example with `unresolved=true`, and prevent them from being presented as fully validated inventory.
- Emit reconciliation events when the missing entity is resolved.

**Conflicting records**

- Resolve conflicts using source authority, source timestamp, and deterministic field-level precedence rules.
- Apply rules such as primary NETCONF inventory taking precedence over secondary SNMP-derived observations only when that precedence is defined for the relevant field and source.
- Retain source provenance and the selected resolution outcome for auditability.
- Avoid relying on a global last-write-wins rule where source clocks or source authority differ.

### 4.5 Temporal versioning

Use **bitemporal data modeling** to distinguish:

- **Effective time:** when a topology fact was true in the network.
- **System/ingestion time:** when the platform received or recorded that fact.

This supports historical questions such as: "What did the topology look like at 10:05 UTC when the alarm occurred?"

A topology query should accept an optional timestamp and resolve relationships valid at that effective time, while retaining the system-time context needed to explain when the platform learned about the fact. SCD Type 2 patterns may be used for suitable dimension-style records, but should not replace bitemporal semantics where both timelines are operationally important.

### 4.6 Linking inventory to KPIs

Associate KPI measurements with immutable inventory entity UUIDs. Maintain explicit mappings from vendor identifiers and source-specific entity references to canonical entity IDs. This allows historical KPI records to remain interpretable after a node is renamed, moved, or decommissioned.

---

## 5. KPI Engine and Data Quality

### 5.1 Storage and processing design

Use **BigQuery** for high-volume performance measurements, analytical queries, aggregation, and reporting across the network.

Organize data into logical layers:

1. **Raw landing / append-only staging:** retain received measurements and ingestion metadata.
2. **Validated and deduplicated layer:** resolve duplicate deliveries and identify the accepted version of each measurement.
3. **Curated KPI layer:** expose normalized, tenant-scoped measurements with formula version, measurement time, ingestion time, and quality metadata.
4. **Rollup layer:** maintain commonly used hourly and daily aggregates for interactive agent queries and reporting.

Partition large measurement tables by an appropriate time column and cluster by tenant and frequently filtered dimensions where workload testing supports the choice. Avoid assuming that a single partitioning or clustering strategy will be optimal for every query pattern.

### 5.2 Late-arriving data

Performance counters may arrive up to two hours late. The platform must preserve the original arrival record and correct affected curated results without creating uncontrolled DML churn.

Recommended pattern:

- Write incoming records to append-only staging.
- Deduplicate and select the accepted measurement version using deterministic keys and source metadata.
- Use controlled, targeted partition repair or merge operations for affected time windows.
- Track the event-time range and partitions affected by each repair.
- Keep historical reprocessing separate from interactive KPI query workloads.
- Use BigQuery reservations, workload separation, and quotas where appropriate to protect interactive query capacity.
- Record repair status and processing lineage so consumers can identify data that is still being corrected.

A representative deduplication pattern is:

```sql
SELECT * EXCEPT(row_num)
FROM (
  SELECT
    measurements.*,
    ROW_NUMBER() OVER (
      PARTITION BY tenant_id, entity_id, metric_name, measurement_time
      ORDER BY source_priority ASC, ingestion_time DESC
    ) AS row_num
  FROM `project.dataset.raw_measurements` AS measurements
)
WHERE row_num = 1;
```

The partition key and ordering rules must be adapted to the source's actual uniqueness and correction semantics. The example is illustrative, not a universal deduplication contract.

### 5.3 KPI windows, formulas, and recalculation

- Process measurements in 15-minute windows aligned with vendor measurement intervals.
- Store formula definitions and versions in a governed formula registry.
- Include the formula version in curated KPI outputs.
- When a formula changes, identify affected metrics and time partitions.
- Execute recalculation as background work using Cloud Run Jobs or an equivalent controlled batch workflow.
- Preserve the previous result lineage or audit record so a recalculated KPI can be explained and reproduced.

### 5.4 KPI quality metadata

Every KPI response must carry explicit quality and provenance information.

| Field | Meaning |
| :--- | :--- |
| `is_complete` | Whether all expected measurement buckets are present |
| `completeness_score` | Numeric measure of received versus expected data, from 0.0 to 1.0 |
| `data_status` | `VALID`, `ESTIMATED`, `INCOMPLETE`, or `UNAVAILABLE` |
| `measurement_window` | Start and end of the measurement period |
| `formula_version` | Formula version used to calculate the KPI |
| `source_provenance` | Source systems and relevant ingestion metadata |
| `last_updated_at` | Time at which the curated result was last updated |

The `completeness_score` must not be interpreted as proof that the KPI value is correct. Completeness, validity, freshness, and source reliability are separate evidence dimensions.

### 5.5 Interactive query performance

Agent-facing KPI tools should query curated and appropriately aggregated datasets rather than repeatedly scanning raw telemetry. Common investigation windows and frequently requested metrics should be supported by tested query patterns and rollups.

Separate interactive queries from bulk backfills and recalculation through workload management, reservations, quotas, and service-level concurrency controls. Do not assume that materialized views can support every rolling-window or window-function query; use them only for query shapes supported by BigQuery's materialized-view capabilities.

---

## 6. Agent Runtime and Engineering Stack

### 6.1 Where the agents run

The agent layer runs on **Google Cloud Run**. It is not a process embedded in BigQuery, Cloud SQL, or the user interface.

Use the following runtime pattern:

- **Agent Access Gateway:** a FastAPI service deployed to Cloud Run. It authenticates the caller, validates role and tenant claims, applies request limits, and invokes the appropriate agent workflow.
- **Specialist agent services:** independently deployable Cloud Run services for Alarm Management, Performance Analysis, and Change Planning.
- **Agent orchestration:** Google ADK for Python, with Gemini models accessed through Vertex AI.
- **MCP tool plane:** private FastAPI/MCP services that expose narrowly scoped topology, KPI, alarm-context, and change-proposal operations.
- **Asynchronous event processing:** Pub/Sub-triggered Cloud Run workers for alarm-driven or other event-driven workflows.
- **Finite background processing:** Cloud Run Jobs for bounded tasks such as scheduled evaluations, bulk context preparation, or reconciliation.

The three specialist roles can share a common Python codebase, typed tool schemas, policy library, and evaluation framework while being deployed as separate services. This provides independent scaling and service identities without creating three unrelated engineering platforms.

### 6.2 Agent technology stack

| Layer | Technology | Responsibility |
| :--- | :--- | :--- |
| Agent framework | Google ADK for Python | Agent definition, workflow orchestration, tool calling, and evaluation |
| Foundation model | Gemini via Vertex AI | Reasoning, summarization, and structured response generation |
| API framework | FastAPI | Agent gateway and service APIs |
| Tool protocol | MCP Python SDK and REST | Standardized, controlled access to platform capabilities |
| Runtime | Cloud Run services | Gateway, specialist agents, and tool services |
| Event processing | Pub/Sub and Cloud Run worker pools / services | Asynchronous alarm and event workflows |
| Batch processing | Cloud Run Jobs | Scheduled and finite processing |
| Session / workflow state | Bounded application state in Cloud SQL or Firestore | Conversation or workflow continuity; not a substitute for the system of record |
| Secrets | Secret Manager | External credentials and sensitive configuration |
| Identity | Dedicated service accounts and IAM | Workload-to-workload authorization |
| Container delivery | Cloud Build and Artifact Registry | Build, version, and deploy container images |
| Observability | Cloud Logging, Cloud Monitoring, Cloud Trace, Error Reporting | Operational telemetry and troubleshooting |

The framework and model are separate concerns: ADK defines and orchestrates the agent workflow; Gemini supplies the model capability through Vertex AI. The model must not receive direct database credentials or unrestricted access to raw storage.

### 6.3 Specialist agent responsibilities

**Alarm Management Agent**

- Receives an alarm investigation request or event.
- Retrieves alarm context and the relevant historical topology snapshot.
- Uses topology and KPI tools to gather evidence around the affected entity and its dependencies.
- Produces a structured assessment, evidence references, uncertainty statements, and recommended next investigative steps.
- Does not directly execute production network changes.

**Performance Analysis Agent**

- Retrieves KPI time series for selected entities, metrics, and time windows.
- Checks completeness, formula version, freshness, and data status.
- Compares relevant entities or periods where the request and available evidence support comparison.
- Produces a performance assessment with supporting measurements and limitations.

**Change Planning Agent**

- Consumes an approved investigation context and proposed objective.
- Retrieves relevant topology and KPI evidence.
- Produces a proposed change specification, impact summary, justification, and validation considerations.
- Submits a proposal or ticket through the authorized proposal tool.
- Cannot apply production changes; production execution requires an explicit human approval and an authorized downstream change process.

### 6.4 Agent construction lifecycle

1. **Define the role and policy.** Specify the agent's purpose, allowed actions, prohibited actions, required evidence, and escalation conditions.
2. **Define typed tools.** Create versioned input/output schemas for topology, KPI, alarm, and change-proposal operations.
3. **Implement the ADK agent.** Configure instructions, tool access, workflow steps, model settings, and bounded iteration behavior.
4. **Build deterministic preprocessing.** Retrieve required alarm or request context before invoking model reasoning wherever possible.
5. **Create evaluation cases.** Use labelled incidents, expected evidence, role-boundary tests, missing-data cases, and adversarial inputs.
6. **Package the service.** Build a container with pinned dependencies and deployable configuration.
7. **Deploy with least privilege.** Assign a dedicated service account, private ingress where appropriate, and explicit tool permissions.
8. **Observe and improve.** Trace model calls and tool executions, measure latency and quality, review failures, and update the evaluation suite before release.

### 6.5 Agent state and memory boundaries

Persist only the state needed to support a defined workflow, such as investigation identifiers, selected evidence references, workflow status, and user-approved context. Use Cloud SQL or Firestore according to the access pattern and consistency requirements.

The agent's conversational state is not the authoritative inventory, KPI, or alarm record. Agents must retrieve current or time-correct evidence from the governed platform tools. Apply retention limits and tenant-scoped access to persisted session data.

---

## 7. API and MCP Tool Design

### 7.1 Core operations

The initial tool surface consists of:

1. `get_node_topology(node_id, depth=2, timestamp=None)`
2. `get_kpi_timeseries(entity_ids, metric_names, start_time, end_time)`
3. `query_alarm_context(alarm_id)`
4. `propose_network_change_ticket(change_spec, justification)`

Each tool must have a versioned schema, documented authorization requirements, bounded inputs, predictable error responses, and traceable execution metadata.

### 7.2 Tool-plane separation

Organize MCP tools into private services by capability:

- **Topology MCP service:** reads tenant-scoped topology from Cloud SQL and uses Redis for eligible cached subgraphs.
- **KPI MCP service:** reads curated KPI datasets and rollups from BigQuery.
- **Alarm and Change Proposal service:** retrieves alarm context and creates proposed tickets or change records through approved interfaces.

The agent invokes tools through the MCP/API layer. It must not connect directly to Cloud SQL or BigQuery using model-generated SQL. Each MCP service independently validates tenant scope, role permissions, input bounds, and request identity.

### 7.3 Example MCP request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_node_topology",
    "arguments": {
      "customer_id": "cust_alpha",
      "node_id": "node_cell_7740",
      "depth": 2,
      "timestamp": "2026-11-10T10:05:00Z"
    }
  },
  "id": "req_091a"
}
```

### 7.4 Example normalized response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "identity": {
      "entity_id": "node_cell_7740",
      "type": "cell",
      "customer_id": "cust_alpha"
    },
    "provenance": {
      "source": "connection_factory_inventory_sync",
      "retrieved_at": "2026-11-10T10:05:02Z",
      "topology_version_id": "topo_v20261110_1000"
    },
    "completeness": {
      "status": "COMPLETE",
      "completeness_score": 1.0,
      "missing_dependencies": []
    },
    "data": {
      "nodes": [],
      "relationships": []
    },
    "errors": []
  },
  "id": "req_091a"
}
```

The empty arrays above are placeholders for the actual returned nodes and relationships. Production responses should also include a schema version, request/trace identifier, and explicit effective timestamp where relevant.

### 7.5 API and tool guardrails

- Maximum topology depth: **3 hops**.
- Per-tool execution timeout: **25 seconds**.
- End-to-end agent response target: **30 seconds**.
- Apply maximum result counts and query-window bounds.
- Validate identifiers and timestamps before accessing data.
- Return explicit `INCOMPLETE`, `UNAVAILABLE`, or error states rather than silently returning partial results as complete.
- Propagate trace identifiers across gateway, agent, MCP service, and data access.
- Use idempotency keys for proposal creation where retries could otherwise create duplicate tickets.

---

## 8. Security, Tenant Isolation, and Governance

### 8.1 Identity and authorization

Authenticate users and upstream callers using OAuth 2.0 / OIDC. Validate JWT signatures, issuer, audience, expiry, and required claims at the gateway.

Relevant claims include:

- `customer_id` or tenant identifier.
- Assigned role, such as `alarm_management`, `performance_analysis`, or `change_planning`.
- User or service identity.
- Any applicable scope or entitlement.

Use dedicated Google Cloud service accounts for the gateway, each specialist agent service, and each MCP tool service. Grant only the permissions required by that workload.

### 8.2 Defense-in-depth tenant isolation

Enforce tenant boundaries at multiple layers:

1. **Identity layer:** bind authenticated requests to an authorized tenant and role.
2. **Gateway layer:** reject missing, invalid, or unauthorized tenant context.
3. **Agent layer:** expose only tools permitted for the agent role and request context.
4. **MCP layer:** independently revalidate tenant and role claims for every tool invocation.
5. **Database layer:** include tenant predicates in repository queries and use database-level controls where appropriate.
6. **BigQuery layer:** enforce tenant-scoped access through authorized views, row-level controls, or isolated datasets/projects as appropriate to the security model.
7. **Cache layer:** include tenant identity in cache keys and prevent cross-tenant cache reuse.
8. **Project and environment layer:** use separate projects or data planes when contractual, regulatory, or operational isolation requires stronger boundaries.

A tenant identifier supplied only as a request parameter is not sufficient authorization. The service must verify that it matches the authenticated identity's permitted tenant scope.

### 8.3 Network and secret controls

- Keep MCP tool services private to the platform service perimeter where feasible.
- Use controlled ingress and service-to-service authentication.
- Store source-system credentials and external API secrets in Secret Manager.
- Do not place secrets in source code, container images, logs, or agent prompts.
- Encrypt data in transit and at rest using Google Cloud security controls and organization-approved key-management policies.
- Use CMEK where required by customer or organizational policy; do not treat CMEK support alone as a reason to select a particular database.
- Audit privileged access, data access, policy changes, and proposed network changes.

### 8.4 Human approval for production actions

Agents may create recommendations and proposed change tickets. They must not directly execute production-impacting changes.

A downstream workflow must enforce:

1. Human review of the proposed change and supporting evidence.
2. Authorization by the appropriate operational role.
3. Change-window and policy validation.
4. Approval and execution through the existing controlled change-management process.
5. Post-change verification and audit recording.

---

## 9. Agent Investigation Behaviour and Evidence Quality

### 9.1 Alarm investigation workflow

Example: an availability alarm is received at 10:05 UTC.

1. **Trigger:** the alarm ingestion workflow publishes an alarm event to Pub/Sub.
2. **Deterministic preprocessing:** an event worker retrieves the alarm record, tenant context, and relevant historical inventory/topology snapshot.
3. **Agent invocation:** the gateway or event worker invokes the Alarm Management Agent with a bounded investigation context.
4. **Topology evidence:** the agent calls `get_node_topology` to identify associated sites and transport dependencies.
5. **KPI evidence:** the agent calls `get_kpi_timeseries` for relevant entities and pre-/post-incident measurement windows.
6. **Evidence assessment:** the agent checks measurement completeness, topology freshness, temporal alignment, and source provenance.
7. **Conclusion or escalation:** the agent returns a supported assessment or explicitly marks the result inconclusive when critical evidence is missing.

### 9.2 Confidence and evidence handling

The confidence score is an advisory assessment of evidence quality. It must not be used as a single absolute circuit-breaker for all agent reasoning.

A proposed initial heuristic weighting is:

| Evidence dimension | Initial weight |
| :--- | :--- |
| KPI completeness | 30% |
| Topology freshness | 25% |
| Temporal alignment | 20% |
| Source reliability | 15% |
| Independent corroboration | 10% |
| **Total** | **100%** |

These weights are starting assumptions for calibration, not statistically validated probabilities. Calibrate them against labelled incidents and operational outcomes. Report the underlying dimensions alongside any aggregate score so that users can understand why evidence is strong or weak.

**Escalation rules**

- A score below **0.85** should trigger a human-review or caution state, not automatically terminate all reasoning.
- If critical telemetry remains unavailable after **two retry iterations**, mark the investigation inconclusive and escalate.
- If topology or KPI data is incomplete, state exactly which evidence is missing and how that limits the conclusion.
- Never invent a root cause to fill an evidence gap.
- Distinguish observed facts, inferred relationships, hypotheses, and recommendations in the agent response.

### 9.3 Standard agent response structure

An investigation response should contain:

1. **Summary:** concise statement of the observed issue.
2. **Scope:** tenant, affected entity, event time, and investigation window.
3. **Evidence:** topology, KPI, alarm, and source references.
4. **Data quality:** completeness, freshness, validity, and known gaps.
5. **Assessment:** supported interpretation and alternative explanations where relevant.
6. **Confidence:** advisory score and component dimensions, if calculated.
7. **Limitations:** missing telemetry, unresolved entities, stale data, or unavailable sources.
8. **Recommended next action:** investigation step or proposed change, clearly distinguished from an executed action.
9. **Escalation status:** whether human review is required.

---

## 10. Performance, Resilience, and Capacity Controls

### 10.1 Protecting the data plane under concurrent agent load

The 100-concurrent-agent scenario must be tested across the full request path. Concurrency at the agent runtime can amplify calls to Redis, Cloud SQL, and BigQuery.

Apply the following controls:

- Per-tenant and per-role request rate limits at the gateway.
- Bounded agent tool-call counts and parallelism.
- Connection pooling and query timeouts for Cloud SQL.
- Redis cache limits, TTLs, request coalescing, and tenant-aware admission controls.
- Curated KPI rollups to avoid repeated raw-data scans.
- BigQuery workload separation, reservations, and quotas for interactive versus batch processing.
- Backpressure and controlled retry policies for Pub/Sub consumers.
- Circuit-breaking or graceful degradation for unavailable dependencies.
- Queue depth, concurrency, and latency monitoring for asynchronous workers.

Do not assume that increasing the number of agent instances automatically increases downstream database capacity. Agent concurrency, tool concurrency, and data-store capacity must be load-tested together.

### 10.2 Resilience and retry policy

- Use bounded retries with exponential backoff and jitter for transient dependency failures.
- Do not retry non-idempotent ticket creation unless an idempotency key is used.
- Route repeatedly failing messages to a dead-letter topic or controlled failure queue.
- Preserve correlation IDs and source event IDs across retries.
- Distinguish transient failure from permanent data-quality failure.
- Return partial evidence only when the response explicitly labels it as partial.

### 10.3 Observability

Instrument the complete path from source ingestion through agent response.

Key measures include:

- Ingestion success/failure rate and processing lag.
- Pub/Sub backlog and oldest unprocessed message age.
- Inventory reconciliation errors and unresolved-entity count.
- KPI ingestion delay, late-arrival rate, repair volume, and completeness.
- BigQuery query latency, bytes scanned, slot consumption, and workload class.
- Cloud SQL query latency, connection saturation, and slow-query rate.
- Redis hit rate, memory utilization, eviction count, and cache invalidation lag.
- Agent invocation count, model latency, tool-call count, retry count, and token usage.
- End-to-end response latency and percentage meeting the 30-second target.
- Escalation rate, inconclusive investigation rate, and human-review outcomes.

Use structured logs and distributed traces with tenant-safe identifiers. Avoid logging raw credentials, unnecessary personal data, or unrestricted payload contents.

---

## 11. Delivery Plan

### Release 1 — MVP

**Scope**

- Single-customer pilot.
- Approximately 1,000 cells.
- Basic topology lookup with depth 2.
- Static KPI retrieval.
- Alarm Management Agent.
- Read-only MCP tools.
- Initial authentication, tenant scoping, logging, and evaluation harness.

**Exit criteria**

- Historical topology reconstruction passes defined correctness tests.
- Read-only role boundaries are enforced.
- Missing-source and timeout scenarios return explicit incomplete-evidence responses.
- The pilot meets agreed latency and reliability targets under representative load.

### Release 2 — Multi-tenant and streaming KPI capability

**Scope**

- Multi-tenant operation for the five-customer planning scenario.
- Full 15-minute KPI ingestion and curation.
- Late-arriving data handling for the two-hour lateness window.
- KPI formula versioning and controlled recalculation.
- Performance Analysis Agent.
- Change Planning Agent limited to proposals and ticket creation.
- Tenant isolation validation across API, agent, MCP, database, cache, and analytics layers.

**Exit criteria**

- Cross-tenant access tests pass.
- Late-data repair produces reproducible curated results.
- Interactive KPI queries remain within agreed performance and cost limits during background processing.
- Change proposals cannot be executed without human approval.

### Release 3 — Multi-agent workflows and operational hardening

**Scope**

- Coordinated workflows across Alarm Management, Performance Analysis, and Change Planning agents.
- Automated evaluation and regression test harnesses.
- Expanded operational dashboards and alerting.
- Concurrency, resilience, and failure-injection testing.
- Capacity and cost optimization based on production-like telemetry.

**Exit criteria**

- Agent handoffs preserve tenant scope, evidence provenance, and authorization.
- Evaluation gates run before production deployment.
- The platform meets agreed service objectives under target concurrency and failure scenarios.
- Operational teams can trace an agent conclusion to the data and tool results used.

---

## 12. Testing and Acceptance Strategy

### 12.1 Functional and data correctness

1. **Historical topology test:** verify that `get_node_topology` reconstructs the correct graph state for a past timestamp despite later inventory updates.
2. **Entity identity test:** verify that KPI records remain linked to the correct immutable entity after rename, movement, or decommissioning.
3. **Deduplication test:** replay duplicate inventory and KPI deliveries and verify idempotent outcomes.
4. **Conflict-resolution test:** provide competing source observations and verify deterministic precedence and provenance.
5. **Late-data test:** inject measurements arriving up to two hours late and verify controlled repair of the affected curated windows.
6. **Formula-version test:** recalculate a KPI after a formula change and verify that the output identifies the correct formula version.

### 12.2 Security and authorization

1. **Tenant isolation test:** verify that a caller cannot retrieve another tenant's topology, KPI, alarm, cache entry, or workflow state.
2. **Role-boundary test:** verify that an Alarm Management Agent cannot invoke a Change Planning operation unless explicitly authorized by policy.
3. **MCP authorization test:** bypass the gateway in a controlled test and verify that the MCP service still rejects unauthorized tenant or role claims.
4. **Production-write test:** verify that no agent identity can execute a production network change directly.
5. **Secret-handling test:** verify that credentials are not exposed in prompts, logs, traces, or error responses.

### 12.3 Resilience and performance

1. **Vendor timeout test:** simulate a 504 response from an inventory source and verify controlled retry and explicit failure reporting.
2. **Dependency degradation test:** simulate Cloud SQL, Redis, or BigQuery latency and verify bounded timeouts and graceful degradation.
3. **Concurrency test:** exercise the 100-concurrent-agent scenario while measuring gateway, agent, MCP, Redis, Cloud SQL, and BigQuery behavior.
4. **Cache correctness test:** update topology and verify that versioning or invalidation prevents stale topology from being returned as current.
5. **End-to-end latency test:** verify the two-hop topology p95 target and 30-second agent response target under representative load.
6. **Queue recovery test:** interrupt an event consumer and verify that Pub/Sub backlog is processed without data loss or duplicate side effects.

### 12.4 Agent quality evaluation

Maintain a versioned evaluation set containing:

- Labelled alarm investigations.
- Known topology and KPI evidence.
- Missing and contradictory telemetry scenarios.
- Historical topology cases.
- Role-boundary and prompt-injection attempts.
- Expected escalation behavior.
- Change proposals that must be rejected or sent for human review.

Evaluate factual grounding, evidence citation, correct uncertainty handling, tool selection, policy compliance, and response latency. A model or prompt change should not be promoted solely because sample answers appear fluent.

---

## 13. Key Architecture Decisions and Reassessment Triggers

| Decision | Baseline | Reassess when |
| :--- | :--- | :--- |
| Topology store | Cloud SQL for PostgreSQL | Measured traversal or write performance cannot meet targets after indexing and query optimization; graph complexity or scale materially increases |
| Topology acceleration | Memorystore for Redis | Cache hit rate, memory cost, invalidation complexity, or latency shows the current approach is ineffective |
| KPI analytics | BigQuery | Workload, latency, or cost tests indicate a different serving pattern is needed |
| Late-data processing | Append-only staging plus deduplication and targeted partition repair | Repair volume or freshness requirements make the current repair process too expensive or slow |
| Agent framework | Google ADK for Python | Evaluation, integration, or operational evidence demonstrates a material limitation |
| Agent runtime | Cloud Run services, worker pools, and Jobs according to workload type | Long-running stateful execution or other runtime needs exceed Cloud Run's fit |
| Model access | Gemini through Vertex AI | Quality, latency, cost, availability, or governance requirements justify a different model strategy |
| Agent permissions | Separate service identities and tool allow-lists | New roles or actions are introduced; permissions must be reviewed rather than inherited broadly |

Architecture changes should be driven by measured workload results, service objectives, security requirements, and total operating cost—not by technology preference alone.

---

## 14. Representative Python Pseudocode

The following pseudocode illustrates the intended control flow. It is conceptual and does not represent a complete implementation or a specific ADK API signature.

```python
async def investigate_alarm(
    alarm_id: str,
    customer_id: str,
    token_claims: dict,
) -> dict:
    # 1. Enforce identity, role, and tenant scope.
    verify_permissions(
        token_claims,
        required_role="alarm_management",
        customer_id=customer_id,
    )

    # 2. Fetch alarm context deterministically.
    alarm = await alarm_repo.get_by_id(
        alarm_id,
        customer_id=customer_id,
    )
    if not alarm:
        raise EntityNotFoundError("Alarm not found")

    # 3. Retrieve bounded topology at the alarm's effective time.
    topology = await topology_client.get_neighbors(
        node_id=alarm.node_id,
        depth=2,
        at_time=alarm.timestamp,
        customer_id=customer_id,
    )

    # 4. Fetch KPI evidence for the relevant entities and time window.
    entity_ids = [node.id for node in topology.nodes]
    kpis = await kpi_client.get_timeseries(
        entity_ids=entity_ids,
        start_time=alarm.timestamp - timedelta(hours=1),
        end_time=alarm.timestamp + timedelta(minutes=15),
        customer_id=customer_id,
    )

    # 5. Assess evidence quality separately from the model's conclusion.
    evidence_quality = assess_evidence_quality(
        topology=topology,
        kpis=kpis,
        alarm=alarm,
    )

    # 6. Return structured evidence for the agent workflow.
    return {
        "alarm": alarm,
        "topology_snapshot": topology,
        "kpi_evidence": kpis,
        "evidence_quality": evidence_quality,
        "requires_human_review": evidence_quality.requires_review,
    }
```

In production, tenant identity should be derived from validated authentication claims and propagated through trusted service context. It must not be trusted solely because it appears in a caller-supplied function argument.

---

## 15. Implementation Principles

The platform should be implemented according to the following principles:

1. **Deterministic data access:** agents reason over governed platform tools, not direct database connections or unrestricted source payloads.
2. **Tenant isolation by design:** every service, query, cache key, and persisted workflow record carries an enforceable tenant boundary.
3. **Evidence before conclusion:** every operational assessment includes provenance, time context, and data-quality indicators.
4. **Bounded autonomy:** agent roles, tools, query depth, execution time, and retries are explicitly limited.
5. **Human control of production changes:** agents propose; authorized operational processes approve and execute.
6. **Workload isolation:** interactive requests are protected from ingestion bursts, backfills, and historical recalculation.
7. **Measured technology choices:** select the simplest architecture that meets tested scale, latency, availability, security, and cost requirements.
8. **Continuous evaluation:** agent changes are tested against labelled operational cases and policy-boundary scenarios before deployment.

---

## 16. Reference Documentation

The following Google Cloud documentation should be used during implementation to confirm current product capabilities, configuration details, and deployment procedures:

- Cloud Run documentation: [https://cloud.google.com/run/docs](https://cloud.google.com/run/docs)
- Cloud Run deployment of ADK agents: [https://cloud.google.com/run/docs/quickstarts/deploy-an-adk-agent](https://cloud.google.com/run/docs/quickstarts/deploy-an-adk-agent)
- Google Agent Development Kit documentation: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- Vertex AI documentation: [https://cloud.google.com/vertex-ai/docs](https://cloud.google.com/vertex-ai/docs)
- Pub/Sub documentation: [https://cloud.google.com/pubsub/docs](https://cloud.google.com/pubsub/docs)
- Cloud SQL for PostgreSQL documentation: [https://cloud.google.com/sql/docs/postgres](https://cloud.google.com/sql/docs/postgres)
- BigQuery documentation: [https://cloud.google.com/bigquery/docs](https://cloud.google.com/bigquery/docs)
- Memorystore for Redis documentation: [https://cloud.google.com/memorystore/docs/redis](https://cloud.google.com/memorystore/docs/redis)
- Model Context Protocol documentation: [https://modelcontextprotocol.io/docs](https://modelcontextprotocol.io/docs)

Product capabilities and service limits can change. Validate the selected deployment configuration against current Google Cloud documentation and the organization's security and networking standards before implementation.