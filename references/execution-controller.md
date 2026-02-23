# Execution Controller

> Execution controller (mandatory path). Used for "plan first, execute second" to prevent skipping steps, missing steps, or false positives.
> This document is the authoritative source for execution flow. In case of conflict with other documents, this file takes precedence.

## Table of Contents

- [Step 1: Mode Determination](#step-1-mode-determination)
- [Step 2: Document Loading](#step-2-document-loading-mandatory-by-mode)
- [Step 3: Reconnaissance](#step-3-reconnaissance)
- [Step 4: Execution Plan](#step-4-execution-plan-with-gate-validation)
- [Step 5: Execution](#step-5-execution)
- [HALT Recovery Strategy](#halt-recovery-strategy)
- [can_report() Checklist](#can_report--pre-report-validation-checklist)
- [Coverage Anti-Inflation Rules](#coverage-anti-inflation-rules)
- [Special Project Type Handling](#special-project-type-handling)

## Step 1: Mode Determination

Mode: `quick | standard | deep`.

The mode determines the depth-cost tradeoff: quick mode sacrifices depth for speed (suitable for CI/CD where fast feedback matters more than exhaustive coverage), while deep mode invests multiple rounds to uncover complex attack chains that single-pass scanning would miss.

Must output:

```text
[MODE] {quick|standard|deep}
```

Special rules:
- Very small projects (<500 LOC): forced quick mode, 1 Agent
- Mixed-language projects: when Phase 0 identifies multiple languages, record them; Agent partitioning prioritizes language boundaries

## Step 2: Document Loading (Mandatory by Mode)

**Upfront loading** (at skill start):

| Mode | Documents |
|------|-----------|
| `quick` | execution-controller.md + agent-contract.md + phase0-attack-surface.md |
| `standard` | quick baseline + coverage-matrix.md |
| `deep` | standard baseline + agent-output-recovery.md |

**Deferred loading** (after [PLAN_ACK]):

| Mode | Documents |
|------|-----------|
| `standard` | phase-definitions.md + multi-round-protocol.md |
| `deep` | phase-definitions.md + multi-round-protocol.md + deep-mode-state-machine.md |

**On-demand loading** (at Phase 4 entry):

| Mode | Documents |
|------|-----------|
| `standard/deep` | validation-agent-contracts.md |

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
| `all_passed` | Three core items completed (modules + entrypoint + dependency) | standard / deep |

### Substantive Constraints (Prevent Step-Skipping)

These constraints exist because LLMs tend to produce plausible-looking "completed" markers without actually doing the work. Requiring concrete artifacts (file:line handlers, name:version dependencies) forces genuine reconnaissance rather than superficial pass-through.

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
phase0_inventory: {modules_inventory, entrypoint_inventory, dependency_inventory, content_type_inventory(optional)}
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
| 5 | Semgrep available | standard/deep: `semgrep --version` succeeds | [HALT] — prompt user to install semgrep |

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
Launch Phase 2 Agents + Semgrep baseline scan (parallel)  [standard/deep only]
    ↓
Agents and Semgrep execute concurrently
    ↓
All Agents completed + Semgrep completed → Phase 2.5
```

> In standard/deep modes, the Semgrep baseline scan launches **in parallel** with Phase 2 business Agents. Semgrep is **mandatory** in standard/deep modes and must complete successfully (completed or partial). Quick mode skips the Semgrep scan and launches Agents directly.

**Semgrep Baseline Command**:

```bash
semgrep scan --config auto --json --output semgrep-baseline.json
```

**Parse Command** (raw output is too large, script parsing required):

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json \
  --min-severity WARNING \
  --exclude-third-party \
  --format json \
  --output semgrep-findings.json
```

Script location: `parse_semgrep_baseline.py` is in the `scripts/` directory of this skill.

**Key parse parameters**:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--min-severity {INFO\|WARNING\|ERROR}` | `INFO` | Minimum severity filter |
| `--exclude-third-party` | `false` | Exclude vendor/third-party directories and minified files |
| `--format {text\|json}` | `text` | Output format. `json` for Phase 4a consumption |
| `--output <path>` | `-` (stdout) | Output file path |
| `--include-path-regex <regex>` | empty | Path whitelist filter (repeatable) |
| `--exclude-path-regex <regex>` | empty | Path blacklist filter (repeatable) |

**Semgrep availability check** (standard/deep, mandatory):

1. Check availability: `which semgrep` or `semgrep --version`
2. If unavailable: trigger [HALT] — prompt user to install semgrep before continuing. Do not proceed to Phase 2
3. If execution errors but has partial output: attempt to parse existing output, set `semgrep_status=partial` (acceptable, audit continues)
4. If execution fails with no output: retry once. If still failing, trigger [HALT] — prompt user to fix semgrep installation

**Accepted `semgrep_status` values by mode**:

| Mode | `completed` | `partial` | `skipped` |
|------|:-----------:|:---------:|:---------:|
| quick | N/A (not executed) | N/A | N/A |
| standard | ✅ | ✅ | ❌ triggers [HALT] |
| deep | ✅ | ✅ | ❌ triggers [HALT] |

## Step 5: Execution

Entry condition: All Step 4 gate validations passed.

> **Phase definitions, transition gates, and no-skip rules**: see [Phase Definitions](phase-definitions.md).

**Quick mode phase summary**: Phase 1 → Phase 2 → Phase 5 (skips Phase 3/4). Quick mode Agents launch without Semgrep; coverage assessed after Agents complete; proceed directly to report.

**Standard/deep mode phase summary**: Phase 1 → Phase 2 (+Semgrep parallel) → Phase 2.5 (merge) → Phase 3 (deep dive) → Phase 4 (validation, load [validation-agent-contracts.md](validation-agent-contracts.md) at entry) → Phase 5 (report).

> **Budget, round strategy, and cross-round state transfer**: see [Multi-Round Protocol](multi-round-protocol.md). Quick reference — Agent counts: quick 1-3, standard/deep by scale (2-9). Round limits: quick 1, standard 2, deep 3. Turns: R1=25, R2=20, R3=15.

> **Deep mode state machine**: see [Deep Mode State Machine](deep-mode-state-machine.md) (deep mode only).

---

## [HALT] Recovery Strategy

When [HALT] is triggered, instead of "blocking everything," execute the corresponding recovery strategy. The goal is resilience: partial results are better than no results, and most blockers have workarounds that preserve audit integrity.

| Trigger Condition | Recovery Strategy |
|-------------------|-------------------|
| Phase 0 incomplete | Supplement missing items and re-evaluate (Phase 0 max 2 retries, 3 total attempts). Each retry **must** include: (a) failure reason from previous attempt, (b) specific improvement strategy (e.g., different Grep patterns, broader file scope), (c) targeted items to complete. Blind re-execution without improvement is prohibited |
| D1-D3 is ❌ | Add targeted Agents and re-evaluate |
| Agent failure | Retry once, then downgrade to ⚠️ and continue |
| Phase 3/4 partial | Record the gap; may continue but report marked "incomplete". Phase 3 partial → report includes "**Deep Dive Incomplete**" watermark + Critical findings confidence capped at `medium`. Phase 4 partial → unvalidated Critical/High auto-downgraded to Medium + `needs_manual` |
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
| 4 | Phases complete | standard/deep: Phase 3/4 [PHASE] markers exist AND operation traces detected (Phase 3: deeper data flow evidence produced for Critical/High findings; Phase 4: ≥1 Validation Agent launched or main thread validation performed) | Execute missing Phase. If markers exist but no operation traces → report auto-tagged as "QUICK_EQUIVALENT" |
| 5 | Dedup complete | Phase 4b dedup executed (standard/deep), both 4a and 4c complete | Execute dedup |
| 6 | D1-D3 met | standard/deep: D1-D3 all ✅ (or ⚠️ with explanation in limitations) | Add Agents |

Quick mode simplified validation: only checks #1, #2, #3.

Supplemental rules:
- If failed Agents exist, must retry or convert to timeout first, and downgrade corresponding dimensions to ⚠️ + explain in limitations
- When D3/D9 is ✅, must include EPR and CRUD consistency statistics (missing means ⚠️ at most)
- When `semgrep_status=completed`, all `semgrep-findings.json` hits must be categorized as confirmed/rejected/needs_manual
- All Critical/High findings must provide a PoC; if not possible, must fill in "reason for non-reproducibility" and downgrade to needs_manual
- Report format must follow [Report Template](report-template.md)
- **Phase Skip Detector**: If main thread output lacks operation traces for Phase 2.5/3/4 (e.g., no "Phase 3 files read", no "Validation Agent launched", no `===MERGE_RESULT===`), trigger [HALT] with `phase_skip_violation`
- **QUICK_EQUIVALENT tag**: When standard/deep mode skips Phase 3/4, the report header must include `⚠️ QUICK_EQUIVALENT: This report was generated without Deep Dive and Validation phases. Findings have not been independently verified.`

---

## Coverage Anti-Inflation Rules

Without these rules, an Agent can claim ✅ coverage for a dimension just by running a few Grep searches — without ever tracing whether the matches actually represent exploitable vulnerabilities. These rules ensure that "covered" means "genuinely analyzed," not "pattern-matched."

Prerequisites for marking a dimension ✅ (meet at least one):
1. At least 1 Sink in that dimension was traced to a Source (complete data flow)
2. At least 3 related Grep searches returned zero hits (proving the absence of that class of Sink)

Dimensions that were only Grep-searched without data flow tracing can be ⚠️ at most.

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
