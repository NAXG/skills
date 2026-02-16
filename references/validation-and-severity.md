# Validation & Severity

> Load this file during Phase 4 (Validation).

## Phase 4 Validation Structure

Phase 4 consists of three sub-steps, where **4a and 4c can execute in parallel, and 4b serves as the final merge step**:

```text
Phase 4a (Semgrep Verification) ─┐
                                  ├→ Phase 4b (Merge Dedup + Calibration) → Phase 4 Complete
Phase 4c (Cross-Validation) ─────┘
```

### Phase 4a: Semgrep Verification

At the start of Phase 4, complete all hit verification from `semgrep-findings.json`. Launched simultaneously with Phase 4c.

Skipped when `semgrep_status=skipped`.

**Phase 4a Batched Routing**:
```text
if semgrep_status == skipped:
    skip
elif semgrep_status == partial:
    main thread verification (only process parsed findings, mark unparsed as needs_manual)
elif semgrep_findings_total <= 15:
    main thread verification (current behavior, unchanged)
elif semgrep_findings_total <= 30:
    1 agent-semgrep-verify
else:
    2 agent-semgrep-verify (grouped by file)
```

**Responsibilities**:
- Verify reachability and evidence completeness for each hit
- Archive each hit as `confirmed | rejected | needs_manual`
- Produce `rule_hotspots` and `file_hotspots`

**Output Contract**:
```text
semgrep_verification:
  semgrep_findings_total: {n}
  confirmed: [finding_id...]
  rejected: [finding_id...]
  needs_manual: [finding_id...]
  unresolved_findings_count: {n}
  rule_hotspots: [{rule_id:count...}]
  file_hotspots: [{file:count...}]
```

**Constraints**:
- When `semgrep_status=completed`, must satisfy `confirmed + rejected + needs_manual = semgrep_findings_total`
- When `semgrep_status=partial`, only archive parsed findings; unresolved portions count toward `needs_manual`
- "Unarchived = ignored" is prohibited
- `rule_hotspots/file_hotspots` are passed to business Agents as priority input (for reference in subsequent rounds)

### Phase 4c: Multi-Agent Cross-Validation

**Input**: Post-Phase 2.5 merged findings list + pre-validation status. Launched simultaneously with Phase 4a.

**Phase 4c Routing Logic**:

Determines validation strategy based on the severity and pre-validation status of findings awaiting validation:

```text
┌─ Critical/High + validation=partial/skip ──→ Cross-validation Agent (full four steps)
├─ Critical/High + validation=pass ──────────→ Main thread spot check (verify data flow key nodes)
├─ Medium + validation=partial/skip ─────────→ Validation Agent batch verification (simplified three steps: 1+2+3)
└─ Medium/Low + validation=pass ─────────────→ Accept pre-validation conclusion, no repeat verification
```

**Four-Step Validation Method** (Cross-validation Agents execute all four steps for Critical/High):

| Step | Verification Item | Judgment Criteria |
|------|-------------------|-------------------|
| 1 | Data flow completeness | No effective truncation between Source and Sink |
| 2 | Defense bypassability | Existing defenses have boundary flaws or bypass paths |
| 3 | Precondition feasibility | Attacker can reach the trigger point (authentication/permission/network conditions) |
| 4 | Impact scope | Maximum damage after exploitation is quantifiable |

All four steps pass: vulnerability confirmed. Any step fails: downgrade or exclude.

**Main Thread Spot Check Rules** (for Critical/High findings with `validation=pass`):
- Randomly sample >= 30% of pass findings (minimum 1)
- Only verify data flow key nodes (Step 1), no full four-step process
- If spot check reveals pre-validation conclusion errors → all pass findings from that Phase 2 Agent are upgraded to needs_validation and reassigned to a Validation Agent for re-verification

**Phase 4c Substance Constraints (Prevent Step-Skipping)**:
- Must provide an independent validation conclusion for each Critical/High finding (cannot just say "confirmed")
- Validation conclusions must reference specific code lines (`file:line`), no vague statements
- Unvalidated Critical/High findings are automatically downgraded to Medium + `needs_manual`

### Phase 4b: Merge Deduplication + Severity Calibration (Final Step)

Phase 4b executes after Phase 4a and Phase 4c are both complete.

**Input**:
1. Phase 4a Semgrep verification results (confirmed/rejected/needs_manual)
2. Phase 4c Validation Agent `===VALIDATION_RESULT===` outputs
3. Main thread spot check results

**Execution Steps**:
1. Collect all Validation Agent outputs
2. Apply validation conclusions: confirmed retained, downgraded update severity, rejected removed
3. Merge Semgrep confirmed findings with business Agent findings
4. Apply [report-template.md](report-template.md) "Cross-Source Deduplication Rules" for deduplication
5. Execute severity secondary calibration (see "Severity Secondary Calibration" section below)
6. Produce the final deduplicated findings list

**Constraints**:
- Deduplication is performed at this stage, no longer deferred to the report stage
- The deduplicated findings list serves as the direct input for Phase 5 report

---

## Severity Level Decision Model

Severity Level = `f(Reachability, Impact Scope, Exploitation Complexity)`

Quick Decision:
- Unauthenticated reachable + RCE/full database read → `Critical`
- Requires authentication but high impact (RCE/full database read) → `High`
- Exploitable but limited impact → `Medium`
- Hard to exploit or hardening recommendation only → `Low/Info`

## Confidence Levels

| Level | Conditions | Maximum Reportable Severity |
|-------|-----------|----------------------------|
| Verified | Complete data flow + no effective defense + exploit constructible | Critical |
| High Confidence | Complete data flow + no effective defense, PoC depends on environment | Critical/High |
| Medium Confidence | Incomplete data flow or bypass conditions not fully confirmed | Medium |
| Needs Verification | Pattern match only, not fully traced | Low/Info |

Hard Rule: Critical/High must reach "High Confidence" or "Verified".
PoC Gate: Critical/High must provide a PoC; if no PoC, must state "Non-Reproducibility Reason" and mark as `needs_manual` or downgrade confidence.

## Severity Secondary Calibration (Cross-Agent)

The main thread executes secondary calibration in Phase 4b "after merge deduplication" to prevent rating drift across different Agents.

Calibration Score:

```text
score = Reachability + Impact Scope + Exploitation Complexity + Defense Friction
```

- Reachability:
  - Unauthenticated reachable: `+2`
  - Low-privilege reachable: `+1`
  - Admin/restricted internal reachable: `+0`
- Impact Scope:
  - RCE/full database read/cross-tenant full data leak: `+3`
  - Partial sensitive data/critical operation abuse: `+2`
  - Information gathering or local impact: `+1`
- Exploitation Complexity:
  - Single request or few repeatable requests: `+0`
  - Multi-step chained exploitation: `-1`
  - Depends on specific environment or strong preconditions: `-2`
- Defense Friction:
  - No effective defense: `+0`
  - Defense exists but reliably bypassable: `+0`
  - Defense exists and bypass requires additional stringent conditions: `-1`

Mapping Rules:

- `score >= 5` → `Critical`
- `score 3-4` → `High`
- `score 1-2` → `Medium`
- `score <= 0` → `Low/Info`

Conflict Resolution:

- Calibrated level differs from initial level by 1: adopt calibrated level
- Differs by >= 2 levels: flag as "rating dispute", explain both assessment rationales in the report
- Multiple instances of the same vulnerability type: unify final level for that type based on highest instance

## Numbering System

| Prefix | CVSS 3.1 | Meaning |
|--------|----------|---------|
| C | 9.0-10.0 | System-level compromise risk |
| H | 7.0-8.9 | Major damage risk |
| M | 4.0-6.9 | Moderate damage |
| L | 0.1-3.9 | Hardening recommendation |

Sorting: impact breadth first, then attack chain root node priority, same-module findings grouped adjacently.

## Attack Chain Construction Rules

For each Critical/High finding:
1. Clarify preconditions (authentication, role, network position)
2. Check if it can be combined with authentication bypass, information disclosure, etc.
3. Verify that upstream exploitation results can serve as downstream input
4. Output independent severity + combined severity (reported separately)

## Rating Consistency Requirements

- Numbering severity: based on "independent exploitability"
- Combined severity: written only in the attack chain section, does not override individual finding numbering
- If new evidence changes reachability, must write back and re-rate
