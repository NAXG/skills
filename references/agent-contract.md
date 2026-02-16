# Agent Contract

> Load this file before launching parallel Agents in Phase 2.

## Contract Text (Injected into Every Agent)

```text
---Agent Contract---
1. Search paths: {paths}. Exclude: node_modules, .git, build, target, bin, obj, dist, vendor, __pycache__, .gradle, coverage, .next, .nuxt, out, public/assets
2. Must use Grep/Glob/Read tools. grep/find/cat in Bash are prohibited.
3. Tool call limits (see "Tool Call Limits" section below), Bash ≤10 calls. max_turns: {N}. Reserve 10 calls for loading language/framework documents.
4. Turn reservation: When turns_used ≥ max_turns-3, stop exploration and produce structured output.
5. Search strategy: Grep to locate line numbers → Read offset/limit for context (±20 lines). Reading >500 lines at once is prohibited.
6. Output: Return using the structured template. Returning large blocks of raw code (>3 lines) is prohibited.
7. Merge report when ≥5 similar vulnerabilities found. For the same pattern across multiple files, list them without deep-diving each one.
8. Sink category upper bound: Max 8 Sink categories per dimension, max 3 instances per category for deep tracing.
9. Data flow tracing: Source → [Transform1 ... TransformN] → Sink, trace at least 3 levels of call chain.
10. Truncation defense: AGENT_RESULT at the beginning, AGENT_RESULT_END sentinel at the end.
11. Anti-hallucination: Every finding must reference actual Read tool output. Guessing paths and reporting unread files are prohibited.
12. Test directory strategy: Exclude test/tests by default; but D7 (hardcoded secrets) and D8 (configuration defects) still require scanning test directories.
13. Pre-validation: Every Critical/High finding must perform inline pre-validation (simplified four-step validation).
    Medium/Low may mark validation: skip. Pre-validation does not consume additional tool call budget—
    use the code context already read when discovering the vulnerability.
---End Contract---
```

### Tool Call Limits

Per Agent **during a single round of execution** (from launch to AGENT_RESULT_END):

| Tool Category | Limit | Description |
|---------------|-------|-------------|
| Grep + Glob + Read | Combined ≤ 60 calls | Search and read operations |
| Bash | ≤ 10 calls | Not counted toward the 60 call limit |
| Edit + Write | 0 calls | Agents must not modify target code |

> When limits are exceeded, the Agent should immediately output currently collected findings and end with AGENT_RESULT_END.

### Sink Standard Classification Table

| Sink Category | Typical Functions/APIs | Associated CWE |
|---------------|----------------------|----------------|
| SQL Sink | execute(), query(), raw() | CWE-89 |
| Command Sink | exec(), system(), popen() | CWE-78 |
| File Sink | open(), readFile(), writeFile() | CWE-22, CWE-73 |
| HTTP Sink | fetch(), request(), redirect() | CWE-918 (SSRF) |
| Deserialization Sink | deserialize(), pickle.loads(), readObject() | CWE-502 |
| Template Sink | render(), render_template_string() | CWE-1336 |
| LDAP Sink | search(), bind() | CWE-90 |
| Crypto Sink | encrypt(), hash(), sign() | CWE-327 |

Select up to 8 Sink categories per dimension, with a maximum of 3 instances per category for full data flow analysis.

### Call Chain Tracing Rules

- Trace at least 3 levels of call chain (Source → intermediate functions → Sink)
- **Chain break handling**: When the call chain cannot be continued due to dynamic dispatch, reflection, callbacks, etc.:
  - Record the breakpoint location (file + line number + break reason)
  - Mark as `chain_status: broken`
  - Does not count as coverage failure, but the finding must note `confidence: medium` (not high)
  - Break reason categories: `reflection` | `dynamic_dispatch` | `callback` | `async_boundary` | `external_library`

## Language/Framework Module Preloading (Mandatory)

**This Agent must load** tech stack-related documents immediately upon launch (not loaded by the main thread):

1. **When a framework is identified, must load the corresponding frameworks/*.md**
   - high confidence (>0.8): must load
   - medium confidence (0.5-0.8): recommended to load
   - Multiple frameworks: sort by priority, load high confidence first
   - Framework and language module selection rules: see [Pattern Library Routing](pattern-library-routing.md)

2. **When a language is identified, must load the corresponding languages/*.md (main document)**
   - Java projects must load `languages/java.md`
   - Python projects must load `languages/python.md`
   - Same for other languages

3. **Budget allocation adjustments**
   - Tool calls ≤60 (previously 50), reserving 10 for document loading
   - max_turns recommendation: R1 Agent = 25 (previously 20), reserving 5 turns for document loading

4. **Preloading priority**
   - P0: Language main document (e.g., languages/java.md)
   - P1: high confidence framework documents
   - P2: medium confidence framework documents
   - P3: Related topic documents (e.g., java_deserialization.md, as needed)

5. **Verification requirements**
   - Agent must report `modules_loaded` in its output
   - If no language/framework documents were loaded, must explain why
   - Must not skip preloading citing "insufficient tool budget"

## R2 Additional Constraints

- Do not re-read `FILES_READ` by default; only allowed for attack chain validation, new finding backtracking, or HOTSPOTS correlation verification, with stated justification
- Full field definitions, data formats, and behavioral rules for cross-round state transfer: see the "Cross-Round State Transfer Protocol" section in execution-controller.md
- Do not reuse `GREP_DONE` by default; only allowed for verifying new evidence or cross-module propagation, with stated justification
- Skip `CLEAN` and `FALSE_POSITIVES` by default; review is allowed when conflicting evidence arises, with the conflict source recorded

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

## Output Template

```text
===AGENT_RESULT===
agent_id: {id}
round: {n}
dimensions: D1,D3,D5
coverage: D1=✅,D3=⚠️,D5=✅
modules_loaded: spring.md,java.md
files_read_count: 23
tool_calls: Grep=18,Glob=5,Read=20,Bash=3
hotspots: file:lines — reason
gaps: D3

[F001] Critical | CWE-89 | SQL Injection in UserController
  file: src/main/java/UserController.java:45-52
  dim: D1
  confidence: high
  source: request.getParameter("id") :42
  sink: jdbcTemplate.query(sql) :50
  flow: :42 → :45(concat) → :50
  evidence: String sql = "SELECT * FROM users WHERE id = " + id;
  impact: Attacker can inject arbitrary SQL
  validation: pass | 1:pass(flow_complete) 2:pass(no_sanitizer) 3:pass(unauth_endpoint) 4:pass(full_db_read)

[F002] ...

===AGENT_RESULT_END===
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| agent_id | Yes | Agent unique identifier |
| round | Yes | Round number |
| dimensions | Yes | List of responsible dimensions |
| coverage | Yes | Coverage status per dimension |
| modules_loaded | Yes | Loaded language/framework modules |
| files_read_count | Yes | Total files read |
| tool_calls | Yes | Tool call counts by category |
| hotspots | No | Recommended hotspots for next round review |
| gaps | No | Dimensions not fully covered |

### Finding Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| [FNNN] | Yes | Sequence number (F001, F002, ...), used for truncation recovery |
| severity | Yes | Critical \| High \| Medium \| Low |
| CWE | Yes | CWE number |
| title | Yes | Vulnerability title |
| file | Yes | File path:line range |
| dim | Yes | Associated dimension |
| confidence | Yes | high \| medium \| low |
| source | Yes | Source description + line number |
| sink | Yes | Sink description + line number |
| flow | Yes | Data flow path (line → line) |
| evidence | Yes | Actual code evidence (≤3 lines) |
| impact | Yes | Impact description |
| validation | Yes (Critical/High) | Pre-validation conclusion. Format: `{overall} \| 1:{result}({reason}) 2:{result}({reason}) 3:{result}({reason}) 4:{result}({reason})`. overall: pass\|partial\|skip. Per-step result: pass\|fail\|uncertain. Medium/Low may mark `skip` |

### Truncation Detection

Truncation detection condition: missing `===AGENT_RESULT_END===`

### Pre-Validation Four-Step Summary

When an Agent discovers a Critical/High vulnerability, it performs in-place pre-validation (simplified version of the four-step validation from validation-and-severity.md) using existing code context:

| Step | Validation Item | Assessment Method |
|------|----------------|-------------------|
| 1 | Data flow completeness | Is there effective truncation in the Source→Sink path? (already have the flow field, just assess) |
| 2 | Protection bypassability | Does a sanitizer/validator exist? If so, can it be bypassed? |
| 3 | Precondition satisfiability | Does the endpoint require authentication? Is it attacker-reachable? |
| 4 | Impact scope | Maximum damage upon successful exploitation? |

`validation` field format:
```
validation: {overall} | 1:{result}({reason}) 2:{result}({reason}) 3:{result}({reason}) 4:{result}({reason})
```

- `overall`: `pass` | `partial` | `skip`
- Per-step `result`: `pass` | `fail` | `uncertain`
- `pass`: All four steps passed; Phase 4 only needs spot-checking
- `partial`: Some steps uncertain; Phase 4 needs focused validation
- `skip`: Agent ran out of tool budget; Phase 4 needs full validation

## Validation Agent Contract (`agent-validate-*`)

**Execution phase**: Phase 4c (Cross-Validation)

Input:
- Findings list (including Phase 2 Agent original output + pre-validation status)
- Phase 2.5 merged_findings context
- Phase 4b severity calibration results

Tasks:
- Perform independent validation for each assigned finding
- Must re-read key code (do not trust Phase 2 Agent's evidence field)
- Output validation conclusions

Constraints:
- max_turns: 15
- Tool calls: Grep+Glob+Read ≤ 40, Bash ≤ 5
- Must not modify the finding's classification (CWE) or type; can only modify severity and confidence
- Each Critical/High must reference specific code lines (file:line)

**Cross-validation principle**:
- Validation Agents **must validate findings from other** Phase 2 Agents (cannot validate their own)
- Assignment strategy: cross-assign by Phase 2 Agent source
- If only 1 Phase 2 Agent: the Validation Agent still performs independent validation (fresh perspective)

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

[V-FNNN] confirmed | {original severity} → {validated severity}
  original: {source_agent_id} [FNNN]
  verification: 1:{result} 2:{result} 3:{result} 4:{result}
  evidence_file: {file}:{line}
  notes: {validation notes}

[V-FNNN] downgraded | {original severity} → {validated severity}
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

**Degradation path**: When a Validation Agent fails or is truncated, fall back to main thread validation without blocking the flow.

### Format Anomaly Handling

Format anomalies (distinct from truncation):
- `===AGENT_RESULT===` exists but key fields are missing (e.g., no agent_id or dimensions)
- Finding format does not match the [FNNN] pattern
- Handling: extract parseable findings; discard unparseable portions and log a warning

## Truncation Handling

If the main thread detects a missing `===AGENT_RESULT_END===`:

1. Check whether the agent_id line exists
2. agent_id exists (mild truncation): preserve coverage and file traces; determine completed finding count via the last `[FNNN]`
3. agent_id missing (severe truncation): forcibly downgrade that Agent's dimensions to ⚠️ and fill gaps in the next round

Constraints:
- Findings in a truncated state must not be directly elevated to Critical/High
- Must not claim "full coverage" for that dimension until recovery is complete
- For detailed recovery process, see [Agent Output Truncation Recovery](agent-output-recovery.md)
