# Multi-Round Protocol

> Extracted from [execution-controller.md](execution-controller.md) Budget & Round Strategy + Cross-Round State Transfer.
> Loaded after [PLAN_ACK] in standard/deep modes.

## Table of Contents

- [Agent Count](#agent-count)
- [Round Limits](#round-limits)
- [Turns Budget](#turns-budget-recommended)
- [R2 Agent Adaptive Allocation](#r2-agent-adaptive-allocation)
- [GAPS Counting Rules](#gaps-counting-rules)
- [Convergence Rules](#convergence-rules)
- [Full Agent Failure Recovery](#full-agent-failure-recovery)
- [Coverage Deadlock Resolution](#coverage-deadlock-resolution)
- [Cross-Round State Transfer Protocol](#cross-round-state-transfer-protocol)

---

## Agent Count

- `standard/deep`: Allocated by project scale
  - Very small (<500 LOC): 1
  - Small (<10K LOC): 2-3
  - Medium (10K-100K LOC): 3-5
  - Large (>100K LOC): 5-9

## Round Limits

- `standard`: max 2 rounds
- `deep`: max 3 rounds

## Turns Budget (Recommended)

- R1 Agent: `max_turns = 25` (reserve 5 turns for language/framework document preloading)
- R2 Agent: `max_turns = 20`
- R3 Agent (attack chain cross-validation only): `max_turns = 15`

## R2 Agent Adaptive Allocation

Allocated by uncovered dimensions and shallow coverage gaps:

- `❌` 0-1 → 1 Agent
- `❌` 2-3 → 2 Agents
- `❌` 4+ or D1/D2/D3 has critical shallow coverage → 3 Agents

## GAPS Counting Rules

GAPS uses non-N/A audit dimensions in D1-D10 as counting units:
- A dimension marked ❌ or ⚠️ counts toward GAPS
- N/A dimensions do not count toward GAPS
- GAPS count = total dimensions in COVERED that are not ✅ and not N/A

## Convergence Rules

**Convergence** = no new Phase 2 Agents are launched for a new Round, but the current Round must complete Phase 3 and Phase 4.

Convergence prevents infinite audit loops while ensuring quality: at some point, additional scanning rounds yield diminishing returns, but the findings already collected still need proper deep-dive analysis and validation before reporting.

- Stop condition: GAPS ≤ 2 or mode maximum rounds reached
- After convergence: current round's Phase 3 focuses on in-depth analysis of discovered findings
- After convergence: current round's Phase 4 completes validation of all findings
- Prioritize filling GAPS and HOTSPOTS; do not repeat the same shallow searches from previous rounds
- **When round limit reached but gaps remain**:
  * If gaps include D1-D3: allow 1 emergency Agent round (targeting only ❌ D1-D3, max_turns=15)
  * If gaps are only D4-D10: may converge; mark as "not met" in report
- Do not skip Phase 3/4 citing "insufficient coverage"
- Do not converge directly from Phase 2 to Report

## Full Agent Failure Recovery

When all Agents have FAILED/TRUNCATED:
1. Do not give up immediately
2. Split dimensions finer and restart 1-2 reduced-scope Agents (halve dimensions + halve max_turns)
3. If still failing → mark report as "audit incomplete," output partial results collected so far

## Coverage Deadlock Resolution

When standard mode has reached the 2-round limit but D1-D3 still has ❌:
- Allow 1 emergency Agent round (targeting only ❌ D1-D3, max_turns=15)
- Or downgrade to ⚠️ and mark as "not met" in report
- Avoid infinite loops

---

## Cross-Round State Transfer Protocol

> Effective only in standard/deep mode. Defines the state transfer format from R(N) → R(N+1).

Without explicit state transfer, each new round starts from scratch — re-reading files already analyzed, re-running Grep patterns already tried, and potentially re-discovering the same false positives. This protocol ensures that subsequent rounds build on previous work rather than repeating it, making multi-round audits efficient and progressively deeper.

### Transfer Mechanism

Cross-round state is injected as a JSON structure into the next round Agent's system prompt:

```json
{
  "round_context": {
    "current_round": 2,
    "previous_rounds": [1],
    "transfer_data": { ... }
  }
}
```

### Required Fields

| Field | Type | Limit | Description |
|-------|------|-------|-------------|
| FILES_READ | `string[]` | ≤100 entries (or directory-aggregated: directory + file count) | List of read file paths; R(N+1) does not re-read by default. When exceeding 100, aggregate by directory (record `dir:count` instead of individual files) |
| COVERED | `Record<string, "✅"\|"⚠️"\|"❌"\|"N/A">` | — | D1-D10 coverage status |
| GAPS | `string[]` | — | Uncovered/partially covered dimension IDs (N/A dimensions excluded) |

### Optional Fields

| Field | Type | Limit | Priority | Description |
|-------|------|-------|----------|-------------|
| CLEAN | `string[]` | — | Low | Files confirmed to have no vulnerabilities |
| FALSE_POSITIVES | `Array<{file, line, reason}>` | — | Low | Excluded false positives |
| HOTSPOTS | `Array<{file, lines, reason}>` | — | High | High-risk hotspot areas |
| GREP_DONE | `Array<{pattern, scope}>` | ≤30 entries | Low | Grep patterns already executed |
| FINDINGS_SUMMARY | `Array<{id, severity, cwe, file, status}>` | ≤30 entries (severity-stratified: all Critical/High retained, Low truncated first) | High | Previous round findings summary |

### Agent Behavioral Rules

1. R(N+1) does not re-read files in FILES_READ by default (unless in HOTSPOTS)
2. R(N+1) must prioritize dimensions listed in GAPS
3. R(N+1) must not repeat searches already in GREP_DONE (unless narrowing scope)
4. R(N+1) should skip CLEAN and FALSE_POSITIVES files (unless new evidence points to them)
5. R(N+1) findings must be cross-checked against FALSE_POSITIVES

### Transfer Integrity Validation

The round controller validates three core fields before injection:
- FILES_READ is non-empty (and ≤100 entries; oldest entries truncated if exceeded, or directory-aggregated when count > 100)
- COVERED contains all D1-D10 keys
- FINDINGS_SUMMARY ≤30 entries (severity-stratified: all Critical/High retained first, then High, then Medium; Low truncated first)

Optional field validation (when present):
- GAPS is consistent with COVERED (GAPS dimensions are ⚠️ or ❌ in COVERED)
- GREP_DONE ≤30 entries (oldest entries truncated if exceeded)

---

## Deep Mode Extensions

> Applies to deep mode only. Extends the round management protocol with agent lifecycle tracking and a structured evaluation rule.

### agent_registry Data Structure

Deep mode maintains an `agent_registry` to track the lifecycle of every Agent across rounds:

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

Rules:
- Only query task_ids present in agent_registry; not_found is treated as invalid result
- All Agents must complete or be marked as timed out, and Semgrep must complete (completed/partial), before entering evaluation
- If any Agent shows failed/sibling_error/not_found: retry once first; if still failing, convert to timeout and downgrade corresponding dimensions to ⚠️

### Three-Question Evaluation Rule

At each ROUND_N_EVALUATION (after output truncation detection and track-based coverage assessment), apply this rule to decide whether another round is needed:

1. Are there planned but unsearched areas remaining?
2. Have all entry points been traced to Sinks?
3. Do high-risk findings have potential cross-module combinations?

Decision logic:
- If **any** of the three questions is YES → launch NEXT_ROUND
- If coverage meets threshold and all three are NO → proceed to Phase 3 (Deep Dive)
- Cannot jump directly from evaluation to Report; must follow the mandatory path: Deep Dive → Validation → Report
