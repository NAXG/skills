# Execution Controller

> Execution controller (mandatory path). Used for "plan first, execute second" to prevent skipping steps, missing steps, or false positives.
> This document is the authoritative source for execution flow. In case of conflict with other documents, this file takes precedence.

## Step 1: Mode Determination

Mode: `quick | standard | deep`.

Must output:

```text
[MODE] {quick|standard|deep}
```

Special rules:
- Very small projects (<500 LOC): forced quick mode, 1 Agent
- Mixed-language projects: when Phase 0 identifies multiple languages, record them; Agent partitioning prioritizes language boundaries

## Step 2: Document Loading (Mandatory by Mode)

**Main thread loading** (execution controller/orchestration layer):
- `quick`
  - Current `SKILL.md`
  - `references/execution-controller.md`
  - `references/agent-contract.md`
  - `references/phase0-attack-surface.md`
- `standard`
  - All `quick` documents
  - `coverage-matrix.md`
  - `references/semgrep-playbook.md`
- `deep`
  - All `standard` documents
  - `references/agent-output-recovery.md`

**Agent loading** (parallel scanning Agents):
- `languages/{language}.md` (main document, required)
- `frameworks/{framework}.md` (based on framework_candidates identification)
- Module selection rules: see [Pattern Library Routing](pattern-library-routing.md)
- **Note**: Tech stack documents are not loaded by the main thread; they are loaded by Agents launched in Phase 2

Must output:

```text
[LOADED] {list of actually Read documents}
```

## Step 3: Reconnaissance

Phase 0 is an embedded sub-phase of Phase 1 (does not produce an independent [PHASE] marker) and must complete the phase0_checklist as a prerequisite for Phase 1 completion.

### Completion Gate Tiers

| Gate | Condition | Applicable Mode |
|------|-----------|-----------------|
| `quick_passed` | `entrypoint_inventory=completed` + `dependency_inventory=completed` | quick |
| `all_passed` | All four items completed | standard / deep |

### Substantive Constraints (Prevent Step-Skipping)

- `entrypoint_inventory=completed` requires: at least 1 concrete handler in `file:line` format; cannot just say "completed"
- `dependency_inventory=completed` requires: at least 1 concrete dependency in `name:version` format; cannot just say "completed"
- Main thread validation: checks whether output contains handlers in `file:line` format and dependencies in `name:version` format

Must output:

```text
[RECON]
Project scale: {X files, Y directories, Z LOC}
Tech stack: {language, framework, version}
Project type: {CMS|Finance|SaaS|Data Platform|Identity|IoT|General Web|Library}
Entry points: {Controller/Router/Handler count}
Key modules: {list}
phase0_inventory: {modules_inventory, entrypoint_inventory, content_type_inventory, dependency_inventory}
phase0_checklist: {quick_passed|all_passed|partial}
```

For detailed reconnaissance steps, see [Phase 0 Attack Surface](phase0-attack-surface.md).

## Step 4: Execution Plan (with Gate Validation)

After generating the execution plan, pause and wait for user confirmation before executing.

Must output:

```text
[PLAN]
Mode: {mode}
Tech stack: {from RECON}
phase0_checklist: {from RECON}
Scan dimensions: {D1-D10}
Agent plan: {dimensions per Agent + max_turns}
Round planning: {R1 -> R2(as needed) -> R3(as needed)}
Report gate: {prerequisites must be met before entering REPORT}
```

Followed by the confirmation marker:

```text
[PLAN_ACK] {confirmed|auto_confirmed|not_confirmed}
```

### Gate Validation (Internal, No Separate Output Marker)

After [PLAN_ACK], the main thread internally validates the following conditions; all must pass before entering Step 5:

| # | Check Item | Condition | Failure Handling |
|---|------------|-----------|------------------|
| 1 | Mode confirmed | [MODE] has been set | Abort |
| 2 | Documents loaded | [LOADED] includes mode-required documents | Supplemental loading |
| 3 | Reconnaissance complete | phase0_checklist meets mode requirements (quick=quick_passed, standard/deep=all_passed or partial_accepted) | Return to Phase 0 |
| 4 | Plan confirmed | [PLAN_ACK] == confirmed or auto_confirmed | Wait for user confirmation |

### Quick Mode Special Rules

- Quick only requires `phase0_checklist=quick_passed` (`entrypoint_inventory` + `dependency_inventory` completed)
- Quick mode `[PLAN_ACK]=auto_confirmed` (does not wait for user confirmation)
- Quick Phase sequence: Phase 1 → Phase 2 → Phase 5 (skips Phase 3/4)

### Semgrep Execution Timing

```text
[PLAN_ACK] confirmed / auto_confirmed
    ↓
[quick mode skips Semgrep, launches Agents directly]
    ↓
Semgrep baseline scan (semgrep scan --config auto --json)  [standard/deep only]
    ↓
Parse results (parse_semgrep_baseline.py)
    ↓
Launch Phase 2 Agents
```

> The Semgrep baseline scan runs after [PLAN_ACK] and before Agent launch (standard/deep modes only). Quick mode skips the Semgrep scan and launches Agents directly. For detailed execution parameters, see [Semgrep Playbook](semgrep-playbook.md).

**Semgrep fault tolerance**: When semgrep is unavailable (command not found, execution failure, timeout), set `semgrep_status=skipped` without blocking Agent launch. Agent scanning proceeds normally; the report notes "Semgrep baseline scan skipped."

## Step 5: Execution

Entry condition: All Step 4 gate validations passed.

### Phase Execution Sequence

| Mode | Phase Sequence | Description |
|------|---------------|-------------|
| quick | Phase 1 → Phase 2 → Phase 5 | Skips Deep Dive and Validation |
| standard | Phase 1 → Phase 2 → Phase 2.5 → Phase 3 → Phase 4 → Phase 5 | Full flow |
| deep | Phase 1 → Phase 2 → Phase 2.5 → Phase 3 → Phase 4 → Phase 5 (multi-round) | Multi-round iteration + strict convergence |

### [PHASE] Unified Marker

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

### Phase 2: Hunt (Agent Scanning)

- First execute the Semgrep baseline scan (standard/deep) or skip it (quick)
- Then launch business Agents (D1-D10 dimension scanning)
- All Agents must complete or be marked as timed out before proceeding to Phase 2.5 (standard/deep) or Phase 5 (quick)
- `quick`: 1 round, coverage-first
- `standard`: 1-2 rounds, balance between coverage and depth
- `deep`: 2-3 rounds, strictly follow the Deep mode state machine (see section at end)

### Phase 2.5: Agent Output Merging (standard/deep)

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

Merged results serve as input for Phase 3/4.

### Phase 3: Deep Dive (standard/deep)

Phase 3 focuses on in-depth analysis of discovered findings.

**Substantive constraints (prevent step-skipping)**:
- Must read ≥3 new files (not in Phase 2's FILES_READ)
- Findings produced must include ≥1 deeper data flow than Phase 2 (call chain depth > Phase 2 average depth)
- If not met, Phase 3 is marked partial, affecting can_report

**Cross-Agent attack chain synthesis** (mandatory sub-step):
- Check whether Critical/High findings from different Agents can be combined
- Combination condition: one finding's output can serve as another's input (e.g., information disclosure → authentication bypass → SQL injection)
- Combinable findings are recorded as attack chains and presented separately in the report

Phase transition gate:
- Phase 3 marked as completed and all P0 files covered
- Phase 3 substantive constraints satisfied

### Phase 4: Validation (standard/deep)

Phase 4 is split into 3 sub-steps, where **4a and 4c can run in parallel, and 4b serves as the final merge step**:

```text
Phase 4a (Semgrep validation) ─┐
                                ├→ Phase 4b (merge dedup + calibration)  → Phase 4 complete
Phase 4c (cross-validation) ───┘
```

**Phase 4a: Semgrep Validation**
- When `semgrep_status=completed`: archive all `semgrep-findings.json` entries (confirmed/rejected/needs_manual)
- When `semgrep_status=partial`: validate only parsed findings; unparsed ones marked `needs_manual`; report notes "Semgrep partially completed"
- When `semgrep_status=skipped`: skip this step

**Phase 4a Agent scheduling** (supports parallelism when Semgrep finding volume is high):
```text
if semgrep_status == skipped:
    skip
elif semgrep_status == partial:
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
- If only 1 Phase 2 Agent: the Validation Agent still performs independent validation (fresh perspective)

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

### Phase 5: Report

Generate the final report. Format follows [Report Template](report-template.md).

### No Phase-Skipping Rules

Hard rules (standard/deep):
- No jumping directly from Phase 1 or Phase 2 to Phase 5
- No skipping Phase 3 (Deep Dive)
- No skipping Phase 4 (Validation)
- If skipping is detected, trigger [HALT]

Quick mode exception:
- Quick mode sequence is Phase 1 → Phase 2 → Phase 5, legitimately skipping Phase 3/4

Minimum phase transition gates:
- `Phase 1 → Phase 2`: phase0_checklist meets mode requirements
- `Phase 2 → Phase 2.5`: All Agents completed or timeout-handled
- `Phase 2 → Phase 5` (quick only): Agents completed and coverage assessed
- `Phase 2.5 → Phase 3`:
  * Coverage assessed
  * D1-D10 status produced
  * Coverage >= mode threshold (see coverage-matrix.md §Overall Scoring Formula for definition)
  * D1-D3 all ✅ or ⚠️ (❌ blocks entry to Phase 3)
  * Hotspots list produced
- `Phase 3 → Phase 4`: Phase 3 marked completed and substantive constraints satisfied
- `Phase 4 → Phase 5`: Phase 4 marked completed, and all Critical/High validated or annotated with "reason for non-reproducibility"

---

## [HALT] Recovery Strategy

When [HALT] is triggered, instead of "blocking everything," execute the corresponding recovery strategy:

| Trigger Condition | Recovery Strategy |
|-------------------|-------------------|
| Phase 0 incomplete | Supplement missing items and re-evaluate (Phase 0 max 2 retries, 3 total attempts) |
| D1-D3 is ❌ | Add targeted Agents and re-evaluate |
| Agent failure | Retry once, then downgrade to ⚠️ and continue |
| Phase 3/4 partial | Record the gap; may continue but report marked "incomplete" |
| phase_skip_violation | Roll back to the skipped Phase and re-execute |

---

## can_report() — Pre-Report Validation Checklist

Internal main thread validation; does not require the LLM to output a can_report() evidence block.

Validation checklist:

| # | Check Item | Condition | Failure Handling |
|---|------------|-----------|------------------|
| 1 | Gates passed | Step 4 gate validation passed | Abort |
| 2 | Coverage met | Overall coverage >= mode threshold (see coverage-matrix.md) | Add rounds/downgrade |
| 3 | All Agents complete | No Agents in RUNNING state | Wait/timeout handling |
| 4 | Phases complete | standard/deep: Phase 3/4 [PHASE] markers exist | Execute missing Phase |
| 5 | Dedup complete | Phase 4b dedup executed (standard/deep), both 4a and 4c complete | Execute dedup |
| 6 | D1-D3 met | standard/deep: D1-D3 all ✅ (or ⚠️ with explanation in limitations) | Add Agents |

Quick mode simplified validation: only checks #1, #2, #3.

Supplemental rules:
- If failed Agents exist, must retry or convert to timeout first, and downgrade corresponding dimensions to ⚠️ + explain in limitations
- When D3/D9 is ✅, must include EPR and CRUD consistency statistics (missing means ⚠️ at most)
- When `semgrep_status=completed`, all `semgrep-findings.json` hits must be categorized as confirmed/rejected/needs_manual
- All Critical/High findings must provide a PoC; if not possible, must fill in "reason for non-reproducibility" and downgrade to needs_manual
- Report format must follow [Report Template](report-template.md)

---

## Coverage Anti-Inflation Rules

Prerequisites for marking a dimension ✅ (meet at least one):
1. At least 1 Sink in that dimension was traced to a Source (complete data flow)
2. At least 3 related Grep searches returned zero hits (proving the absence of that class of Sink)

Dimensions that were only Grep-searched without data flow tracing can be ⚠️ at most.

---

## Budget & Round Strategy

### Agent Count

- `quick`: Fixed 1-3 (1 for very small projects, otherwise 2-3)
- `standard/deep`: Allocated by project scale
  - Small (<10K LOC): 2-3
  - Medium (10K-100K LOC): 3-5
  - Large (>100K LOC): 5-9

### Round Limits

- `quick`: max 1 round
- `standard`: max 2 rounds
- `deep`: max 3 rounds

### Turns Budget (Recommended)

- R1 Agent: `max_turns = 25` (reserve 5 turns for language/framework document preloading)
- R2 Agent: `max_turns = 20`
- R3 Agent (attack chain cross-validation only): `max_turns = 15`

### R2 Agent Adaptive Allocation

Allocated by uncovered dimensions and shallow coverage gaps:

- `❌` 0-1 → 1 Agent
- `❌` 2-3 → 2 Agents
- `❌` 4+ or D1/D2/D3 has critical shallow coverage → 3 Agents

### GAPS Counting Rules

GAPS uses non-N/A audit dimensions in D1-D10 as counting units:
- A dimension marked ❌ or ⚠️ counts toward GAPS
- N/A dimensions do not count toward GAPS
- GAPS count = total dimensions in COVERED that are not ✅ and not N/A

### Convergence Rules

**Convergence** = no new Phase 2 Agents are launched for a new Round, but the current Round must complete Phase 3 and Phase 4.

- Stop condition: GAPS ≤ 2 or mode maximum rounds reached
- After convergence: current round's Phase 3 focuses on in-depth analysis of discovered findings
- After convergence: current round's Phase 4 completes validation of all findings
- Prioritize filling GAPS and HOTSPOTS; do not repeat the same shallow searches from previous rounds
- **When round limit reached but gaps remain**:
  * If gaps include D1-D3: allow 1 emergency Agent round (targeting only ❌ D1-D3, max_turns=15)
  * If gaps are only D4-D10: may converge; mark as "not met" in report
- Do not skip Phase 3/4 citing "insufficient coverage"
- Do not converge directly from Phase 2 to Report

### Full Agent Failure Recovery

When all Agents have FAILED/TRUNCATED:
1. Do not give up immediately
2. Split dimensions finer and restart 1-2 reduced-scope Agents (halve dimensions + halve max_turns)
3. If still failing → mark report as "audit incomplete," output partial results collected so far

### Coverage Deadlock Resolution

When standard mode has reached the 2-round limit but D1-D3 still has ❌:
- Allow 1 emergency Agent round (targeting only ❌ D1-D3, max_turns=15)
- Or downgrade to ⚠️ and mark as "not met" in report
- Avoid infinite loops

---

## Cross-Round State Transfer Protocol

> Effective only in standard/deep mode. Defines the state transfer format from R(N) → R(N+1).

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
| FILES_READ | `string[]` | ≤50 entries | List of read file paths; R(N+1) does not re-read by default |
| COVERED | `Record<string, "✅"\|"⚠️"\|"❌"\|"N/A">` | — | D1-D10 coverage status |
| GAPS | `string[]` | — | Uncovered/partially covered dimension IDs (N/A dimensions excluded) |

### Optional Fields

| Field | Type | Limit | Description |
|-------|------|-------|-------------|
| CLEAN | `string[]` | — | Files confirmed to have no vulnerabilities |
| FALSE_POSITIVES | `Array<{file, line, reason}>` | — | Excluded false positives |
| HOTSPOTS | `Array<{file, lines, reason}>` | — | High-risk hotspot areas |
| GREP_DONE | `Array<{pattern, scope}>` | ≤30 entries | Grep patterns already executed |
| FINDINGS_SUMMARY | `Array<{id, severity, cwe, file, status}>` | ≤20 entries | Previous round findings summary |

### Agent Behavioral Rules

1. R(N+1) does not re-read files in FILES_READ by default (unless in HOTSPOTS)
2. R(N+1) must prioritize dimensions listed in GAPS
3. R(N+1) must not repeat searches already in GREP_DONE (unless narrowing scope)
4. R(N+1) should skip CLEAN and FALSE_POSITIVES files (unless new evidence points to them)
5. R(N+1) findings must be cross-checked against FALSE_POSITIVES

### Transfer Integrity Validation

The round controller validates before injection:
- FILES_READ is non-empty (and ≤50 entries; oldest entries truncated if exceeded)
- COVERED contains all D1-D10 keys
- GAPS is consistent with COVERED (GAPS dimensions are ⚠️ or ❌ in COVERED)
- GREP_DONE ≤30 entries (oldest entries truncated if exceeded)
- FINDINGS_SUMMARY ≤20 entries (retained in descending severity order if exceeded)

---

## Deep Mode State Machine (deep mode only)

### State Diagram

```text
PHASE_1_RECON
  → ROUND_N_RUNNING
  → ROUND_N_EVALUATION
  → NEXT_ROUND (as needed)
  → DEEP_DIVE (Phase 3)  [mandatory]
  → VALIDATION (Phase 4)  [mandatory]
  → REPORT
```

### State: ROUND_N_RUNNING

Rules:
- Agents execute in parallel
- Must maintain agent_registry (structure below)
- Only allowed to query task_ids in agent_registry; not_found is treated as invalid result

#### agent_registry Data Structure

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

- Semgrep scanning executes in Phase 2; validation is unified in Phase 4
- All Agents must complete or be marked as timed out before entering evaluation
- Final report must not be generated before Agents complete
- If any Agent shows failed/sibling_error/not_found: retry once first; if still failing, convert to timeout and downgrade corresponding dimensions to ⚠️

### State: ROUND_N_EVALUATION

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

### State: NEXT_ROUND

Rules:
- Only fill gaps and hotspots; do not repeat previous round's shallow searches
- R2/R3 Agent count and turns per "Budget & Round Strategy" section
- Hard cap: quick=1, standard=2, deep=3

### State: REPORT

Precondition: can_report() validation checklist all passed.

If any condition is not met, return to NEXT_ROUND or annotate limitations before reporting.

---

## Special Project Type Handling

### Library Projects (No HTTP Entry Points)

Detection condition: entrypoint_inventory shows HTTP entry points = 0, but exported public APIs ≥ 5

Handling:
- D2 (Authentication), D3 (Authorization), D6 (SSRF) set to N/A
- Focus on D1 (Injection), D4 (Deserialization), D5 (File Operations), D7 (Cryptography)
- Entry point definition switches to public API functions

### Very Small Projects (<500 LOC)

- Forced quick mode, 1 Agent
- Phase 0 simplified to file list + dependency list only

### Mixed-Language Projects

- When Phase 0 identifies multiple languages, each language's corresponding Agent loads its own language module
- Agent partitioning prioritizes language boundaries over dimensions
