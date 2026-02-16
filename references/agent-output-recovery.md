# Agent Output Truncation Recovery Protocol

> When Agent output is truncated due to token limits, follow this protocol to recover.

## Truncation Detection

Output is considered truncated when the `===AGENT_RESULT_END===` termination marker is missing.

## Recovery Process

### Case 1: Mild Truncation (agent_id line exists)

1. Determine the number of completed findings via the last complete `[FNNN]`
2. Issue a resume request:

**Resume Request Template:**
```
RESUME_REQUEST
Agent-ID: [Original Agent ID]
Last-Complete-Finding: FNNN
Remaining-Dimensions: [Incomplete dimensions]
Resume-Action: continue_from_finding_N+1
```

3. Resume Agent continues output from N+1

### Case 2: Severe Truncation (even the agent_id line is missing)

1. Do not issue a resume
2. Downgrade the entire Agent dimension ⚠️
3. Fill gaps in the next round or via an emergency Agent

### Case 3: Two Consecutive Truncations

- Same Agent truncated twice in a row → limit output (reduce Evidence detail, max 2 lines of code per finding)
- Adjust strategy: split dimensions and distribute across multiple Agents

## Handling Truncated Findings in Phase 4

| Finding Status | Phase 4 Handling |
|----------------|-----------------|
| Complete (full finding block) | Normal validation flow |
| Truncated but Source+Sink identifiable | Supplementary validation, annotate `originally_truncated: true` |
| Truncated with incomplete Source/Sink | Mark as `needs_reaudit`, exclude from final report |

## Report Constraints

The final report must disclose:
- List of Agents that experienced truncation and their recovery status
- Potential coverage gaps caused by truncation
- Number of findings that could not be recovered
