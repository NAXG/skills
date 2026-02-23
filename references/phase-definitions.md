# Phase Definitions

> Extracted from [execution-controller.md](execution-controller.md) Step 5.
> Loaded after [PLAN_ACK] in standard/deep modes.

## Table of Contents

- [Phase Execution Sequence](#phase-execution-sequence)
- [PHASE Unified Marker](#phase-unified-marker)
- [Phase 2: Hunt](#phase-2-hunt-agent-scanning)
- [Phase 2.5: Agent Output Merging](#phase-25-agent-output-merging-standarddeep)
- [Phase 3: Deep Dive](#phase-3-deep-dive-standarddeep)
- [Phase 4: Validation](#phase-4-validation-standarddeep)
- [Phase 5: Report](#phase-5-report)
- [No Phase-Skipping Rules](#no-phase-skipping-rules)

---

## Phase Execution Sequence

| Mode | Phase Sequence | Description |
|------|---------------|-------------|
| quick | Phase 1 → Phase 2 → Phase 5 | Skips Deep Dive and Validation |
| standard | Phase 1 → Phase 2 → Phase 2.5 → Phase 3 → Phase 4 → Phase 5 | Full flow |
| deep | Phase 1 → Phase 2 → Phase 2.5 → Phase 3 → Phase 4 → Phase 5 (multi-round) | Multi-round iteration + strict convergence |

## [PHASE] Unified Marker

Output a unified marker after each phase completes:

```text
[PHASE] phase:{N} status:{completed|partial} next:{N+1|report|halt} evidence:{...}
```

Examples:
```text
[PHASE] phase:2 status:completed next:2.5 evidence:agents=3,findings=12,coverage=7/10
[PHASE] phase:2.5 status:completed next:3 evidence:merged_findings=10,dedup_removed=2,pre_validated=6,needs_validation=4
[PHASE] phase:3 status:completed next:4 evidence:deep_files=5,new_findings=3
[PHASE] phase:4 status:completed next:5 evidence:confirmed=8,rejected=2,needs_manual=1,validation_agents=2,pre_validated=5
```

Quick mode examples:
```text
[PHASE] phase:1 status:completed next:2 evidence:phase0=quick_passed,handlers=12
[PHASE] phase:2 status:completed next:report evidence:agents=2,findings=8,coverage=8/10
```

## Phase 2: Hunt (Agent Scanning)

- Launch business Agents (D1-D10 dimension scanning) and Semgrep baseline scan **in parallel** (standard/deep), or Agents only (quick)
- All Agents must complete or be marked as timed out, **and** Semgrep must complete (completed/partial), before proceeding to Phase 2.5 (standard/deep) or Phase 5 (quick)
- `quick`: 1 round, coverage-first
- `standard`: 1-2 rounds, balance between coverage and depth
- `deep`: 2-3 rounds, strictly follow the [Deep Mode State Machine](deep-mode-state-machine.md)

## Phase 2.5: Agent Output Merging (standard/deep)

After all Agents complete and before coverage assessment, perform output merging:

1. **Collect**: Gather all Agent `===AGENT_RESULT===` outputs
2. **Truncation detection**: Check whether each Agent's `===AGENT_RESULT_END===` exists
3. **Format validation**: Verify completeness of agent_id, dimensions, coverage fields
4. **Merge findings**: Unify numbering of all Agent [FNNN] entries, remove malformed entries
5. **Update COVERED**: Aggregate D1-D10 status based on each Agent's coverage
6. **Pre-validation statistics**: Summarize validation status of each finding
   - pre_validated_count: number of findings with validation=pass
   - needs_validation_count: number of findings with validation=partial or skip
   - These statistics serve as input for Phase 4c routing

**Mandatory output marker**:

```text
===MERGE_RESULT===
merged_findings_count: {n}
dedup_removed_count: {n}
pre_validated_count: {n}
needs_validation_count: {n}
coverage_summary: D1={status},...,D10={status}
hotspots_count: {n}
===MERGE_RESULT_END===
```

**Non-conforming output handling**: When Agent output lacks the `[FNNN]` structured format, it is treated as truncated output and handled via the recovery flow. No free-form parsing is attempted.

**Same Root Cause operational definition**:
- **Primary criterion**: Same file + line range (±5 lines) = same root cause → merge, retain highest severity
- Same Source parameter affects ≥2 different Sinks = same root cause → merge, retain highest severity

Merged results serve as input for Phase 3/4.

## Phase 3: Deep Dive (standard/deep)

Phase 3 focuses on in-depth analysis of discovered findings.

**Adaptive depth by finding count**:
- **Critical/High ≤ 2**: Simplified Deep Dive — perform data flow completion only, skip attack chain synthesis
- **Critical/High ≥ 3**: Full Deep Dive — complete all sub-steps including attack chain synthesis

**Substantive constraints (prevent step-skipping)**:
- **Hotspot-driven targeting**: Must cover all HOTSPOTS flagged by Phase 2/2.5. If no hotspots exist, must trace the complete cross-file data flow for every Critical/High finding in D1-D3
- **Depth metric**: depth = number of method boundaries crossed in a call chain. Phase 3 must produce at least 1 flow with depth > the deepest flow in Phase 2 for the same dimension
- **Evidence depth requirement**: Phase 3 must produce more complete data flow evidence for each Critical/High finding than Phase 2 provided (e.g., deeper call chain, additional intermediate transforms, cross-file flow completion)
- If not met, Phase 3 is marked partial → report must include a "**Deep Dive Incomplete**" watermark, and all Critical findings have confidence capped at `medium`

**Cross-Agent attack chain synthesis** (mandatory when Critical/High ≥ 3; skipped when Critical/High ≤ 2):
- Check whether Critical/High findings from different Agents can be combined
- **Combination pattern library (extensible)**:
  1. Auth bypass (D2) + any other vuln → chain (auth bypass amplifies all downstream impact)
  2. Information disclosure (D7/D8) + Auth bypass (D2) → chain (leaked credentials enable auth bypass)
  3. SSRF (D6) + internal service vuln → chain (SSRF as pivot to internal attack surface)
  4. File upload (D5) + path traversal (D5) → chain (upload + traversal = arbitrary file write)
  5. Injection (D1) + privilege escalation (D3) → chain (injection in low-priv context + privesc = full compromise)
  6. Business logic bypass (D9) + payment/transaction → chain (business logic flaw enables financial fraud)
  7. Stored XSS/SQLi (D1) + admin trigger → chain (second-order attack via stored payload)
  8. Supply chain compromise (D10) + code execution → chain (compromised dependency enables persistent backdoor)
  9. LLM prompt injection + tool invocation → chain (prompt injection leverages tool access for data exfiltration)
- Each chain must document: **pre-conditions**, **step sequence**, and **impact amplification factor** (combined severity vs. individual severities)
- Combinable findings are recorded as attack chains and presented separately in the report

Phase transition gate:
- Phase 3 marked as completed and all P0 files covered
- Phase 3 substantive constraints satisfied

## Phase 4: Validation (standard/deep)

**Phase 4 Fast Track** (small finding sets):
```text
total_findings ≤ 5 AND no Critical → main thread validates directly, no Validation Agent launched
total_findings ≤ 5 AND has Critical → launch 1 Validation Agent for Critical findings only
otherwise → full 4a + 4c parallel → 4b pipeline
```

Phase 4 is split into 3 sub-steps, where **4a and 4c can run in parallel, and 4b serves as the final merge step**:

**Timeout handling**: When a Phase 4 sub-step times out, fall back to main thread validation for its remaining work. Timeout events are recorded in the Phase Completion Ledger.

```text
Phase 4a (Semgrep validation) ─┐
                                ├→ Phase 4b (merge dedup + calibration)  → Phase 4 complete
Phase 4c (cross-validation) ───┘
```

**Phase 4a: Semgrep Validation**
- When `semgrep_status=completed`: archive all `semgrep-findings.json` entries (confirmed/rejected/needs_manual)
- When `semgrep_status=partial`: validate only parsed findings; unparsed ones marked `needs_manual`; report notes "Semgrep partially completed"

> `semgrep_status=skipped` is not permitted in standard/deep modes (blocked at Phase 2 entry).

**Phase 4a Agent scheduling** (supports parallelism when Semgrep finding volume is high):
```text
if semgrep_status == partial:
    main thread validation (process only parsed findings)
elif semgrep_findings_total <= 15:
    main thread validation (current behavior, unchanged)
elif semgrep_findings_total <= 30:
    1 agent-semgrep-verify
else:
    2 agent-semgrep-verify (grouped by file)
```

**Phase 4c: Multi-Agent Cross-Validation**

Route based on pre-validation status to determine validation strategy (see validation-and-severity.md for details).

**Phase 4c Agent count decision**:
```text
needs_full_validation = count of Critical/High where validation ≠ pass
needs_batch_validation = count of Medium where validation ≠ pass

if needs_full_validation == 0:
    main thread spot-checks Critical/High (validation=pass), no Agents needed
elif needs_full_validation <= 5:
    1 Validation Agent
elif needs_full_validation <= 12:
    2 Validation Agents
else:
    3 Validation Agents

if needs_batch_validation > 10:
    additional 1 Batch Validation Agent (handles Medium findings)
```

**Cross-validation assignment strategy**:
- Validation Agents **must validate findings from other** Phase 2 Agents (cannot validate their own)
- Cross-assign by Phase 2 Agent source
  - E.g., if Phase 2 has agent-r1-01, agent-r1-02, agent-r1-03
  - Validation Agent A validates findings from agent-r1-02 and agent-r1-03
  - Validation Agent B validates findings from agent-r1-01
- If only 1 Phase 2 Agent: the Validation Agent must independently re-read all critical code paths (cannot rely on Phase 2 Agent's evidence), and must execute the full 4-step validation for every Critical/High finding

**Grouping strategy** (reduce redundant code reads):
- Findings from the same file/module should be assigned to the same Validation Agent where possible
- Use `file_hotspots` (produced by Phase 4a) as the grouping basis

**Degradation path**: When a Validation Agent fails or is truncated, fall back to main thread validation without blocking the flow.

**Phase 4b: Merge Dedup + Severity Calibration (Final Step)**

Phase 4b executes after both 4a and 4c are complete.

**Input sources**:
1. Phase 4a Semgrep validation results (confirmed/rejected/needs_manual)
2. Phase 4c Validation Agent `===VALIDATION_RESULT===` outputs
3. Main thread spot-check results

**Merge logic**:
1. Collect all Validation Agent outputs
2. Apply validation conclusions: keep confirmed, update severity for downgraded, remove rejected
3. Merge with Semgrep confirmed findings
4. Apply the "cross-source deduplication rules" from [report-template.md](report-template.md)
5. Execute severity recalibration from [validation-and-severity.md](validation-and-severity.md)
6. Produce the final findings list

**Phase 4 substantive constraints (prevent step-skipping)**:
- Must provide an independent validation conclusion for each Critical/High finding (cannot just say "confirmed")
- Validation conclusions must reference specific code lines (`file:line`); cannot be vague
- Unvalidated Critical/High findings are automatically downgraded to Medium + `needs_manual`

Phase transition gate:
- Phase 4 marked as completed
- All Critical/High findings validated or annotated with "reason for non-reproducibility"
- For validation rules, see [Validation & Severity](validation-and-severity.md)

## Phase 5: Report

Generate the final report. Format follows [Report Template](report-template.md).

## No Phase-Skipping Rules

Phases 3 (Deep Dive) and 4 (Validation) are where raw findings get stress-tested. Without them, the report is essentially a list of pattern-match guesses — many will be false positives, and exploitability hasn't been confirmed. Skipping these phases is the single most common way an LLM-driven audit degrades into a superficial scan.

Hard rules (standard/deep):
- No jumping directly from Phase 1 or Phase 2 to Phase 5
- No skipping Phase 3 (Deep Dive)
- No skipping Phase 4 (Validation)
- If skipping is detected, trigger [HALT]

Quick mode exception:
- Quick mode sequence is Phase 1 → Phase 2 → Phase 5, legitimately skipping Phase 3/4

Minimum phase transition gates:
- `Phase 1 → Phase 2`: phase0_checklist meets mode requirements
- `Phase 2 → Phase 2.5`: All Agents completed or timeout-handled, **and** Semgrep completed (completed/partial)
- `Phase 2 → Phase 5` (quick only): Agents completed and coverage assessed
- `Phase 2.5 → Phase 3`:
  * Coverage assessed
  * D1-D10 status produced
  * Coverage >= mode threshold (see coverage-matrix.md §Overall Scoring Formula for definition)
  * D1-D3 all ✅ or ⚠️ (❌ blocks entry to Phase 3) — Injection, Authentication, and Authorization are the three vulnerability categories that attackers exploit most frequently and with the highest impact. An audit that misses any of them provides a false sense of security.
  * Hotspots list produced
- `Phase 3 → Phase 4`: Phase 3 marked completed and substantive constraints satisfied
- `Phase 4 → Phase 5`: Phase 4 marked completed, and all Critical/High validated or annotated with "reason for non-reproducibility"
