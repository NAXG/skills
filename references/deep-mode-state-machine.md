# Deep Mode State Machine

> Extracted from [execution-controller.md](execution-controller.md). Deep mode only.
> Loaded after [PLAN_ACK] in deep mode.

---

## State Diagram

```text
PHASE_1_RECON
  → ROUND_N_RUNNING
  → ROUND_N_EVALUATION
  → NEXT_ROUND (as needed)
  → DEEP_DIVE (Phase 3)  [mandatory]
  → VALIDATION (Phase 4)  [mandatory]
  → REPORT
```

## State: ROUND_N_RUNNING

Rules:
- Agents execute in parallel
- Must maintain agent_registry (structure below)
- Only allowed to query task_ids in agent_registry; not_found is treated as invalid result

### agent_registry Data Structure

| Field | Type | Description |
|-------|------|-------------|
| agent_id | string | Agent unique identifier (e.g., "agent-r1-01") |
| task_id | string | Corresponding Task ID |
| status | enum | PENDING \| RUNNING \| COMPLETED \| FAILED \| TRUNCATED |
| round | number | Round number |
| assigned_dimensions | string[] | Assigned audit dimensions |
| output_status | enum | COMPLETE \| TRUNCATED \| MISSING |
| findings_count | number | Number of findings produced |
| started_at | string | Start timestamp |
| completed_at | string \| null | Completion timestamp |

- Semgrep scanning launches in parallel with Agents during Phase 2; validation is unified in Phase 4
- All Agents must complete or be marked as timed out, and Semgrep must complete (completed/partial), before entering evaluation
- Final report must not be generated before Agents complete
- If any Agent shows failed/sibling_error/not_found: retry once first; if still failing, convert to timeout and downgrade corresponding dimensions to ⚠️

## State: ROUND_N_EVALUATION

Execute first:
- Output truncation detection (see `references/agent-output-recovery.md`)
- Track-based coverage assessment (see `coverage-matrix.md` "Track-Based Coverage Assessment" section)

Three-question rule (any YES → NEXT_ROUND):
1. Are there planned but unsearched areas remaining?
2. Have all entry points been traced to Sinks?
3. Do high-risk findings have potential cross-module combinations?

State transition rules:
- If any of the three questions is YES → NEXT_ROUND
- If coverage meets threshold → DEEP_DIVE (Phase 3)
- Cannot jump directly from ROUND_N_EVALUATION to REPORT
- Must follow the mandatory path: DEEP_DIVE → VALIDATION → REPORT

## State: NEXT_ROUND

Rules:
- Only fill gaps and hotspots; do not repeat previous round's shallow searches
- R2/R3 Agent count and turns per [Multi-Round Protocol](multi-round-protocol.md)
- Hard cap: quick=1, standard=2, deep=3

## State: REPORT

Precondition: can_report() validation checklist all passed.

If any condition is not met, return to NEXT_ROUND or annotate limitations before reporting.
