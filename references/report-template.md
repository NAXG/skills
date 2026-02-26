# Report Template

> Load this file during Phase 5 (Report).

## Mode Branch Description

Report content branches by audit mode:

| Section | standard | deep |
|---------|----------|------|
| Executive Summary | Required | Required |
| Finding Statistics | Required | Required |
| Coverage Matrix | Required | Required |
| Vulnerability Details | Required | Required |
| Audit Limitations | Required | Required |
| Control-driven Evidence | Required | Required |
| Semgrep Verification Evidence | Required | Required |
| Attack Chain Analysis | Required | Required |
| Attack Path Scoring | Optional | Required |

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

---

## Extended Sections

````markdown
### Control-driven Evidence (D3/D9)
| Dimension | Total Endpoints | Audited Endpoints | EPR | CRUD Resource Types | Conclusion |
|-----------|----------------|-------------------|-----|---------------------|------------|
| D3 | {n} | {n} | {n%} | {n} | ✅/⚠️/❌ |
| D9 | {n} | {n} | {n%} | {n} | ✅/⚠️/❌ |

### Semgrep Verification Evidence
| Item | Value |
|------|-------|
| semgrep_status | {completed/partial} |
| semgrep_findings_total | {n} |
| confirmed | {n} |
| rejected | {n} |
| needs_manual | {n} |
| unresolved_findings_count | {n} |

Constraints:
- D3/D9 marked as `✅` must include EPR and CRUD statistics; if missing, downgrade to `⚠️`
- When `semgrep_status=completed`, `unresolved_findings_count` must be `0`
- When `semgrep_status=completed`, `confirmed + rejected + needs_manual = semgrep_findings_total`
- When `semgrep_status=partial`, explain the partial completion reason and number of unresolved findings in Audit Limitations
- `Critical/High` with `PoC Status=not_reproducible` must include "Non-Reproducibility Reason" and must not be marked as "verified"

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

---

## Report Completeness Checklist

The following items are **mandatory** — absence of any item invalidates the report:

- [ ] Executive Summary with all required fields
- [ ] Finding Statistics table
- [ ] Coverage Matrix with D1-D10 status
- [ ] Vulnerability Details for every finding (with Data Flow + Evidence + PoC)
- [ ] Audit Limitations section
- [ ] Semgrep Verification Evidence

The following items are **optional/extended** — enhance report quality but do not invalidate if absent:

- [ ] Attack Path Scoring (required for deep mode, optional for standard)
- [ ] Control-driven Evidence (D3/D9)
````
