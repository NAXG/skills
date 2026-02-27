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
- [can_report() Checklist](#can_report--pre-report-completeness-check)
- [Coverage Anti-Inflation Rules](#coverage-anti-inflation-rules)
- [Special Project Type Handling](#special-project-type-handling)

## Step 1: Mode Determination

Mode: `standard | deep`.

The mode determines the depth-cost tradeoff: standard mode provides full OWASP coverage in 1-2 rounds, while deep mode invests multiple rounds to uncover complex attack chains that single-pass scanning would miss.

Must output:

```text
[MODE] {standard|deep}
```

Special rules:
- Very small projects (<500 LOC): use standard mode with 1 Agent, simplified reconnaissance
- Mixed-language projects: when reconnaissance identifies multiple languages, record them; Agent partitioning prioritizes language boundaries

## Step 2: Document Loading (Mandatory by Mode)

**Upfront loading** (at skill start):

| Mode | Documents |
|------|-----------|
| `standard` | execution-controller.md + agent-contract.md + recon-attack-surface.md + coverage-matrix.md |
| `deep` | standard baseline + agent-output-recovery.md |

**Deferred loading** (after [PLAN_ACK]):

| Mode | Documents |
|------|-----------|
| `standard` | phase-definitions.md + multi-round-protocol.md |
| `deep` | phase-definitions.md + multi-round-protocol.md |

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

Reconnaissance is the first step of Phase 1 (does not produce an independent [PHASE] marker) and must complete the recon_checklist as a prerequisite for Phase 1 completion.

### Completion Gate Tiers

| Gate | Condition | Applicable Mode |
|------|-----------|-----------------|
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
recon_inventory: {modules_inventory, entrypoint_inventory, dependency_inventory, content_type_inventory(optional)}
recon_checklist: {all_passed|partial}
```

For detailed reconnaissance steps, see [Reconnaissance: Attack Surface](recon-attack-surface.md).

## Step 4: Execution Plan (with Gate Validation)

After generating the execution plan, pause and wait for user confirmation before executing.

Must output:

```text
[PLAN]
Mode: {mode}
Tech stack: {from RECON}
recon_checklist: {from RECON}
Scan dimensions: {D1-D10}
Agent plan: {dimensions per Agent + max_turns}
Round planning: {R1 -> R2(as needed) -> R3(as needed)}
Report gate: {prerequisites must be met before entering REPORT}
```

Followed by the confirmation marker:

```text
[PLAN_ACK] {confirmed|not_confirmed}
```

### Gate Validation (Internal, No Separate Output Marker)

After [PLAN_ACK], the main thread internally validates the following conditions; all must pass before entering Step 5:

| # | Check Item | Condition | Failure Handling |
|---|------------|-----------|------------------|
| 1 | Mode confirmed | [MODE] has been set | Abort |
| 2 | Documents loaded | [LOADED] includes mode-required documents | Supplemental loading |
| 3 | Reconnaissance complete | recon_checklist meets mode requirements (standard/deep=all_passed or partial_accepted) | Return to reconnaissance |
| 4 | Plan confirmed | [PLAN_ACK] == confirmed | Wait for user confirmation |
| 5 | Semgrep available | `semgrep --version` succeeds | [HALT] — prompt user to install semgrep |

### Semgrep Execution Timing

```text
[PLAN_ACK] confirmed
    ↓
Launch Phase 2 Agents + agent-semgrep-scan (all parallel)
    ↓
Business Agents and agent-semgrep-scan execute concurrently
    ↓
All Agents completed + agent-semgrep-scan completed → Phase 2.5
```

> The Semgrep baseline scan is executed by a **dedicated `agent-semgrep-scan`**, launched **in parallel** with Phase 2 business Agents. This keeps the main thread free during the scan. Semgrep is **mandatory** and must complete successfully (completed or partial).

**agent-semgrep-scan responsibilities** (see [Agent Contract § agent-semgrep-scan](agent-contract.md#agent-semgrep-scan)):

1. Run the semgrep baseline scan
2. Parse the output using the script
3. Return `semgrep_status` and the path to `semgrep-findings.ison`

**Semgrep availability check** (mandatory, performed by main thread before [PLAN_ACK]):

1. Check availability: `which semgrep` or `semgrep --version`
2. If unavailable: trigger [HALT] — prompt user to install semgrep before continuing. Do not proceed to Phase 2
3. Agent execution errors but has partial output: attempt to parse existing output, set `semgrep_status=partial` (acceptable, audit continues)
4. Agent execution fails with no output: retry once. If still failing, trigger [HALT] — prompt user to fix semgrep installation

**Accepted `semgrep_status` values by mode**:

| Mode | `completed` | `partial` | `skipped` |
|------|:-----------:|:---------:|:---------:|
| standard | ✅ | ✅ | ❌ triggers [HALT] |
| deep | ✅ | ✅ | ❌ triggers [HALT] |

## Step 5: Execution

Entry condition: All Step 4 gate validations passed.

> **Phase definitions, transition gates, and no-skip rules**: see [Phase Definitions](phase-definitions.md).

**Standard/deep mode phase summary**: Phase 1 → Phase 2 (+Semgrep parallel) → Phase 2.5 (merge) → Phase 3 (deep dive) → Phase 4 (validation, load [validation-agent-contracts.md](validation-agent-contracts.md) at entry) → Phase 5 (report).

> **Budget, round strategy, and cross-round state transfer**: see [Multi-Round Protocol](multi-round-protocol.md). Agent counts: standard/deep by scale (2-9). Round limits: standard 2, deep 3. Turns: R1=25, R2=20, R3=15.

> **Deep mode extensions**: see [Multi-Round Protocol § Deep Mode Extensions](multi-round-protocol.md#deep-mode-extensions) (deep mode only).

---

## [HALT] Recovery Strategy

When [HALT] is triggered, instead of "blocking everything," execute the corresponding recovery strategy. The goal is resilience: partial results are better than no results, and most blockers have workarounds that preserve audit integrity.

| Trigger Condition | Recovery Strategy |
|-------------------|-------------------|
| Reconnaissance incomplete | Supplement missing items and re-evaluate (reconnaissance max 2 retries, 3 total attempts). Each retry **must** include: (a) failure reason from previous attempt, (b) specific improvement strategy (e.g., different Grep patterns, broader file scope), (c) targeted items to complete. Blind re-execution without improvement is prohibited |
| D1-D3 is ❌ | Add targeted Agents and re-evaluate |
| Agent failure | Retry once, then downgrade to ⚠️ and continue |
| Phase 3/4 partial | Record the gap; may continue but report marked "incomplete". Phase 3 partial → report includes "**Deep Dive Incomplete**" watermark + Critical findings confidence capped at `medium`. Phase 4 partial → unvalidated Critical/High auto-downgraded to Medium + `needs_manual` |
| phase_skip_violation | Roll back to the skipped Phase and re-execute |

---

## can_report() — Pre-Report Completeness Check

Internal main thread validation before entering Phase 5. Quality enforcement is handled by each Phase's exit gate (see [Phase Definitions](phase-definitions.md)); `can_report()` only verifies that all Phases actually executed and the minimum coverage invariant holds.

Validation checklist:

| # | Check Item | Condition | Failure Handling |
|---|------------|-----------|------------------|
| 1 | Phase markers complete | [PHASE] markers exist for Phase 2, 2.5, 3, 4 | Execute missing Phase |
| 2 | Phase status check | If any Phase has `status:partial` → mark report as "**INCOMPLETE**" | Proceed but add watermark |
| 3 | D1-D3 met | D1-D3 all ✅ (or ⚠️ with explanation in limitations) | Add Agents |

> **Rationale**: Previous checks (gate validation, coverage threshold, Agent completion, dedup completion) are now enforced at Phase transition gates — see [Phase Definitions](phase-definitions.md) §Minimum phase transition gates. This prevents duplicated validation logic and ensures quality is checked at the point of action rather than deferred to report time.

---

## Coverage Anti-Inflation Rules

Without these rules, an Agent can claim ✅ coverage for a dimension just by running a few Grep searches — without ever tracing whether the matches actually represent exploitable vulnerabilities. These rules ensure that "covered" means "genuinely analyzed," not "pattern-matched."

Prerequisites for marking a dimension ✅ (meet at least one):
1. At least 1 Sink in that dimension was traced to a Source (complete data flow), **and** when Grep hit files ≥ 10, the trace rate (files with traced data flows / files with Grep hits) must be ≥ 30%
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

- Use standard mode with 1 Agent
- Reconnaissance simplified to file list + dependency list only

### Mixed-Language Projects

- When reconnaissance identifies multiple languages, each language's corresponding Agent loads its own language module
- Agent partitioning prioritizes language boundaries over dimensions
