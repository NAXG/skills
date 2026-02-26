# Validation Agent Contracts

> Extracted from [agent-contract.md](agent-contract.md).
> Loaded on-demand at Phase 4 entry in standard/deep modes.

## Table of Contents

- [Semgrep Verification Agent](#semgrep-verification-agent-agent-semgrep-verify)
- [Validation Agent Contract](#validation-agent-contract-agent-validate)

---

## Semgrep Verification Agent (`agent-semgrep-verify`)

**Execution phase**: Phase 4a (Validation — Semgrep Verification)

Purpose: During the unified Phase 4 validation stage, verify all hits in the parsed `semgrep-findings.json`.

Input:
- `semgrep-findings.json` (produced by Phase 2)
- Read code evidence (Read/Grep)

Must output:

```text
===SEMGREP_VERIFY===
semgrep_findings_total: {n}
confirmed: [{finding_id,...}]
rejected: [{finding_id,...}]
needs_manual: [{finding_id,...}]
unresolved_findings_count: {n}
rule_hotspots: [{rule_id:count,...}]
file_hotspots: [{file:count,...}]
===END_SEMGREP_VERIFY===
```

Rules:
- Every finding must be categorized as `confirmed/rejected/needs_manual`
- When `semgrep_status=completed`: `confirmed + rejected + needs_manual = semgrep_findings_total`
- No "unarchived and ignored" findings allowed
- `rule_hotspots/file_hotspots` provided for next round reference

---

## Validation Agent Contract (`agent-validate-*`)

**Execution phase**: Phase 4c (Cross-Validation)

Input:
- Findings list (including Phase 2 Agent original output + pre-validation status)
- Phase 2.5 merged_findings context

Tasks:
- Perform independent validation for each assigned finding
- Must re-read key code (do not trust Phase 2 Agent's evidence field)
- Output validation conclusions

Constraints:
- max_turns: 15
- Tool calls: Grep+Glob+Read ≤ base(20) + per_finding(8), capped at 60, Bash ≤ 5
- Must not modify the finding's classification (CWE) or type
- **Validation Agents do not assign or modify severity levels.** Severity is determined solely by Phase 4b calibration. Validation Agents output a verdict (`confirmed | downgraded | rejected`) and four-step assessment results, which Phase 4b uses as input to its scoring formula.
- Each Critical/High must reference specific code lines (file:line)

**Cross-validation principle** — having a different Agent validate findings catches both false positives (the original Agent's confirmation bias) and false negatives (things the original Agent overlooked in the same code area):
- Validation Agents **must validate findings from other** Phase 2 Agents (cannot validate their own)
- Assignment strategy: cross-assign by Phase 2 Agent source
- If only 1 Phase 2 Agent: the Validation Agent must independently re-read all critical code paths (cannot rely on Phase 2 Agent's evidence), and must execute the full 4-step validation for every Critical/High finding

**Grouping strategy** (reduce redundant code reads):
- Findings from the same file/module should be assigned to the same Validation Agent where possible
- Use `file_hotspots` (produced by Phase 4a) as the grouping basis

**Output template**:

```text
===VALIDATION_RESULT===
agent_id: {agent_id}
round: {n}
validated_count: {n}
source_agents: {list of validated Phase 2 Agents}

[V-FNNN] confirmed
  original: {source_agent_id} [FNNN]
  verification: 1:{result} 2:{result} 3:{result} 4:{result}
  evidence_file: {file}:{line}
  notes: {validation notes}

[V-FNNN] downgraded
  original: {source_agent_id} [FNNN]
  verification: 1:{result} 2:{result} 3:{result} 4:{result}
  reason: {downgrade reason + code evidence}
  evidence_file: {file}:{line}

[V-FNNN] rejected
  original: {source_agent_id} [FNNN]
  verification: 1:{result}
  reason: {rejection reason}

===VALIDATION_RESULT_END===
```

> **Note**: Validation Agents output only a verdict (`confirmed`, `downgraded`, or `rejected`) — not a new severity level. The four-step verification results are passed to Phase 4b, which applies the scoring formula to determine final severity. `downgraded` means the validation found issues (e.g., a step failed) that should reduce confidence; the actual severity recalculation happens in Phase 4b.

**Degradation path**: When a Validation Agent fails or is truncated, fall back to main thread validation without blocking the flow.
