# Report Template

> Load this file during Phase 5 (Report).

## Mode Branch Description

Report content branches by audit mode:

| Section | quick | standard | deep |
|---------|-------|----------|------|
| Executive Summary | Required | Required | Required |
| Finding Statistics | Required | Required | Required |
| Coverage Matrix | Required | Required | Required |
| Vulnerability Details | Required | Required | Required |
| Audit Limitations | Required | Required | Required |
| Execution Gate Evidence Details | Skip | Required | Required |
| Phase Completion Ledger | Skip | Required | Required |
| Control-driven Evidence | Skip | Required | Required |
| Semgrep Verification Evidence | Skip | Required | Required |
| Validation Agent Verification Evidence | Skip | Required | Required |
| Source Summary | Skip | Required | Required |
| Attack Chain Analysis | Skip | Required | Required |
| Attack Path Scoring | Skip | Optional | Required |
| Attack Cost Analysis | Skip | Optional | Required |
| Attack Timeline Simulation | Skip | Optional | Recommended (only for Critical findings) |

---

## Full Report Template

````markdown
# Security Audit Report

## Executive Summary
- Project: {project_name}
- Code Size: ~{n}K LOC
- Tech Stack: {stack}
- Audit Mode: {mode}
- Audit Rounds: {rounds} rounds, {agent_count} Agents, {total_turns} tool calls
- Coverage: {n}/{m} dimensions (N/A dimensions excluded from denominator)
- framework_candidates: {id:confidence list}
- loaded_framework_modules: {frameworks/*.md list}
- loaded_language_modules: {languages/*.md list}

## Finding Statistics
| Severity | Count |
|----------|-------|
| Critical | {n} |
| High | {n} |
| Medium | {n} |
| Low | {n} |
| **Total** | **{n}** |

## Coverage Matrix
| # | Dimension | Status | Finding Count |
|---|-----------|--------|---------------|
| D1 | Injection | ✅/⚠️/❌ | {n} |
| D2 | Authentication | ✅/⚠️/❌/N/A | {n} |
| D3 | Authorization | ✅/⚠️/❌/N/A | {n} |
| D4 | Deserialization | ✅/⚠️/❌/N/A | {n} |
| D5 | File Operations | ✅/⚠️/❌/N/A | {n} |
| D6 | SSRF | ✅/⚠️/❌/N/A | {n} |
| D7 | Cryptography | ✅/⚠️/❌/N/A | {n} |
| D8 | Configuration | ✅/⚠️/❌/N/A | {n} |
| D9 | Business Logic | ✅/⚠️/❌/N/A | {n} |
| D10 | Supply Chain | ✅/⚠️/❌/N/A | {n} |

> N/A dimensions show `-` for finding count. Coverage = ✅ count / (10 - N/A count).
> D1/D2/D3 cannot be marked as N/A (except for library projects, see execution-controller.md).

## Vulnerability Details

### [C-01] {Vulnerability Title} (CVSS {score})
- **File**: `{path}:{line}`
- **Type**: {vulnerability_type}
- **Confidence**: {confidence_level}
- **Data Flow**:
  ```
  Source: {source}
  → {transform_1}
  → {transform_2}
  → Sink: {sink}
  ```
- **Evidence**:
  ```{lang}
  {actual code from Read tool, max 3 lines}
  ```
- **PoC**:
  ```http
  POST /search HTTP/1.1
  Host: {target_host}
  Content-Type: application/x-www-form-urlencoded
  Authorization: Bearer {token_if_needed}

  text={payload}
  ```
  - Expected Result: {expected_result}
  - Actual Result: {actual_result}
- **PoC Status**: {provided|not_reproducible}
- **Non-Reproducibility Reason**: {reason_if_not_reproducible}
- **Impact**: {impact_description}

## Audit Limitations
- **Uncovered Dimensions**: {dimensions not reaching ✅ and reasons}
- **N/A Dimensions**: {dimensions marked N/A and rationale}
- **Unaudited Modules/Files**: {omissions due to time or context constraints}
- **Static Analysis Limitations**: {invisible factors such as runtime configuration, third-party services, dynamic loading}
````

> **Quick mode ends here.** The following sections are required only for standard/deep modes.

---

## Standard/Deep Extended Sections

````markdown
## Execution Gate Evidence (Required)
- plan_ack: {confirmed|not_confirmed}
- plan_ack_time: {timestamp}
- can_report: {true|false}

### Phase Execution Evidence (Mandatory Check)

| Phase | [PHASE] Marker | Key Output | Status |
|-------|---------------|------------|--------|
| Phase 1 (Recon) | ✓/✗ | phase0_inventory, phase0_checklist | {status} |
| Phase 2 (Hunt) | ✓/✗ | coverage_matrix, hotspots, D1-D10 status | {status} |
| Phase 2.5 (Merge) | ✓/✗ | merged_findings, dedup_count | {status} |
| Phase 3 (Deep Dive) | ✓/✗ | deep_dive_findings, attack_chains | {status} |
| Phase 4 (Validation) | ✓/✗ | semgrep_verified, validated_findings, validation_agents | {status} |
| Phase 5 (Report) | ✓/✗ | security-audit-report.md | {status} |

**Constraints**:
- If any Phase's [PHASE] marker is missing, the report must be marked as "**INCOMPLETE**"
- Missing Phase 3 or Phase 4 [PHASE] marker = **Report Invalid**
- Phase 3 status = partial → Report header must include: `⚠️ DEEP DIVE INCOMPLETE: Critical findings have confidence capped at medium`
- Report generated without Phase 3/4 execution → header must include: `⚠️ QUICK_EQUIVALENT: This report was generated without Deep Dive and Validation phases`

### Phase Completion Ledger (Required)
| phase | status(completed/partial) | evidence |
|-------|---------------------------|----------|
| Phase 1 (Recon) | {status} | {phase1_evidence} |
| Phase 2 (Hunt) | {status} | {phase2_evidence} |
| Phase 2.5 (Merge) | {status} | {merge_evidence} |
| Phase 3 (Deep Dive) | {status} | {phase3_evidence} |
| Phase 4 (Validation) | {status} | {phase4_evidence} |
| Phase 5 (Report) | {status} | {phase5_evidence} |

### Agent Runtime Status
| agent_id | task_id | status(completed/timeout/failed) | retries | resolution |
|----------|---------|-----------------------------------|---------|------------|
| {agent_1} | {task_1} | {status} | {n} | {normal|retried_ok|downgraded_to_timeout} |

### Phase 0 Completeness (Attack Surface Mapping)
| Item | Status | Description |
|------|--------|-------------|
| modules_inventory | completed/partial | {core/plugins/extensions/tests/examples/config/ci/container} |
| entrypoint_inventory | completed/partial | {http/mq/rpc/scheduled/deserialization} |
| content_type_inventory | completed/partial | {xml/json/form/custom} |
| dependency_inventory | completed/partial | {deps_total + high_risk_components} |
| phase0_checklist | quick_passed/all_passed/partial/partial_accepted | {gate_status} |

### Control-driven Evidence (D3/D9)
| Dimension | Total Endpoints | Audited Endpoints | EPR | CRUD Resource Types | Conclusion |
|-----------|----------------|-------------------|-----|---------------------|------------|
| D3 | {n} | {n} | {n%} | {n} | ✅/⚠️/❌ |
| D9 | {n} | {n} | {n%} | {n} | ✅/⚠️/❌ |

### Semgrep Verification Evidence (If Enabled)
| Item | Value |
|------|-------|
| semgrep_status | {completed/partial} |
| semgrep_findings_total | {n} |
| confirmed | {n} |
| rejected | {n} |
| needs_manual | {n} |
| unresolved_findings_count | {n} |

### Validation Agent Verification Evidence (If Enabled)

| Item | Value |
|------|-------|
| pre_validated_count | {number of findings with validation=pass} |
| needs_validation_count | {number of findings with validation=partial/skip} |
| validation_agents_launched | {number of Validation Agents launched} |
| spot_check_count | {number of main thread spot checks} |
| spot_check_pass_rate | {spot check pass rate} |

| agent_id | source_agents | validated_count | confirmed | downgraded | rejected |
|----------|---------------|-----------------|-----------|------------|----------|
| {agent_validate_1} | {source_agents} | {n} | {n} | {n} | {n} |
| {agent_validate_2} | {source_agents} | {n} | {n} | {n} | {n} |
| Main thread spot check | — | {n} | {n} | {n} | {n} |

Constraints:
- `can_report` admission is governed by [Execution Controller](execution-controller.md)'s `can_report()`; this template only records execution and gate evidence
- `phase0_checklist` must be `all_passed` or `partial_accepted`
- If any `Phase 1-4` status is not `completed`, the report can only serve as an "interim result" and must not be marked as final
- **Phase 3 and Phase 4 [PHASE] markers are mandatory; missing them invalidates the report**
- D3/D9 marked as `✅` must include EPR and CRUD statistics; if missing, downgrade to `⚠️`
- Any `failed/not_found/sibling_error` must reflect the resolution in the `resolution` field
- If any Agent was converted to `timeout`, the impact scope must be explained in "Audit Limitations"
- When `semgrep_status=completed`, `unresolved_findings_count` must be `0`
- When `semgrep_status=completed`, `confirmed + rejected + needs_manual = semgrep_findings_total`
- When `semgrep_status=partial`, explain the partial completion reason and number of unresolved findings in Audit Limitations
- `Critical/High` with `PoC Status=not_reproducible` must include "Non-Reproducibility Reason" and must not be marked as "verified"
- Validation Agent Verification Evidence section: must include per-Agent validation statistics when `validation_agents_launched > 0`
- If spot checks reveal pre-validation errors (spot_check_pass_rate < 100%), the impact must be explained in Audit Limitations

## Source Summary (Semgrep x Agents Merged)
| Source | Raw Finding Count | Deduplicated Count | confirmed | needs_manual | rejected | Notes |
|--------|-------------------|---------------------|-----------|--------------|----------|-------|
| semgrep_verify | {n} | {n} | {n} | {n} | {n} | {note} |
| business_agents | {n} | {n} | {n} | {n} | {n} | {note} |
| validation_agents | — | — | {n} | — | {n} | Cross-validation conclusions (confirmed/downgraded/rejected) |
| cross_source_overlap | {n} | {n} | {n} | {n} | {n} | Same issue overlapping across sources |
| final_merged | {n} | {n} | {n} | {n} | {n} | Final report figures |

### Cross-Source Deduplication Rules

**"Same Issue" Criteria** (any one condition met = same issue):

| Condition | Description |
|-----------|-------------|
| Same file + same line number | Regardless of source or CWE differences, findings at the same file and line are treated as the same issue |
| Same CWE + same function + same data flow | Even with slight line number deviation (±5 lines), if the Source→Sink data flow is identical, it is the same issue |
| Same Root Cause | Multiple findings caused by the same root cause (e.g., the same unfiltered input parameter affecting multiple Sinks) are merged into one issue, taking the highest severity |

**Deduplication Priority Rules**:
1. **Severity**: For multiple findings of the same issue, retain the highest severity
2. **Source Attribution**: The final finding annotates all sources that discovered the issue (e.g., `sources: [semgrep, agent-r1-02]`)
3. **Evidence Merging**: Merge Evidence and PoC from all sources, selecting the most complete version
4. **Confidence**: Issues cross-validated by multiple sources can have confidence upgraded by one level (e.g., medium → high)

Constraints:
- `final_merged.dedup` must equal `Total` in "Finding Statistics"
- `cross_source_overlap` must be executed based on the deduplication rules above
- Must not provide only final totals without source-level breakdown

## Attack Chain Analysis

### Chain 1: {chain_title} (CVSS {combined_score})
```
{step_1} → {step_2} → {step_3} → {final_impact}
```

## Attack Path Scoring

### [AP-01] {attack_path_title}
- **Entry Point**: `{entrypoint}`
- **Preconditions**: {preconditions}
- **Path Length**: {steps_count} steps
- **Authentication Requirement**: {none|user|admin} ({score_auth}/3)
- **Request Complexity**: {single|few|multi} ({score_request}/3)
- **Interaction Dependency**: {none|low|high} ({score_interaction}/3)
- **Exploitation Threshold**: {low|medium|high} ({score_skill}/3)
- **Attack Path Total Score**: {total_score}/12
- **Attacker Gain**: {attacker_gain}

## Attack Cost Analysis
| Attack Path | Required Privileges | Time Cost | Tool Cost | Success Rate | Estimated Gain |
|-------------|-------------------|-----------|-----------|--------------|----------------|
| {path_name_1} | {none/user/admin} | {time_1} | {cost_1} | {success_rate_1} | {gain_1} |
| {path_name_2} | {none/user/admin} | {time_2} | {cost_2} | {success_rate_2} | {gain_2} |

## Attack Timeline Simulation
### Scenario: {scenario_name}
1. `{t0}` Attacker completes entry point reconnaissance: {recon_action}
2. `{t1}` Sends exploitation request: {exploit_action}
3. `{t2}` Gains initial capability: {initial_access}
4. `{t3}` Lateral/vertical movement: {movement}
5. `{t4}` Achieves final impact: {final_impact_detail}

---

## Report Completeness Checklist

The following items are **mandatory** — absence of any item invalidates the report:

- [ ] Executive Summary with all required fields
- [ ] Finding Statistics table
- [ ] Coverage Matrix with D1-D10 status
- [ ] Vulnerability Details for every finding (with Data Flow + Evidence + PoC)
- [ ] Audit Limitations section
- [ ] Phase Completion Ledger (standard/deep)
- [ ] Phase Execution Evidence showing all [PHASE] markers (standard/deep)
- [ ] Validation Agent Verification Evidence (standard/deep, when validation agents launched)

The following items are **optional/extended** — enhance report quality but do not invalidate if absent:

- [ ] Attack Timeline Simulation
- [ ] Attack Path Scoring (required for deep mode, optional for standard)
- [ ] Attack Cost Analysis (required for deep mode, optional for standard)
- [ ] Source Summary cross-source breakdown
- [ ] Semgrep Verification Evidence (required for standard/deep)
````
