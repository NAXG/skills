# Agent Output Truncation Recovery Protocol

> When Agent output is truncated due to token limits, follow this protocol to recover.

## Proactive Truncation Prevention

Agents should estimate output size **before** producing final output:

1. **Estimation formula**: `estimated_tokens = findings_count × 300 + 200 (header overhead)`
2. **Threshold**: If `estimated_tokens > 40%` of remaining context budget, apply compression:
   - Reduce evidence to 1 line per finding (most critical line only)
   - Merge similar findings (same CWE + same file → single entry with line range)
   - Truncate flow field for Low/Medium findings to `Source → Sink` (remove intermediates)
3. **Timing**: This estimation happens before writing `===AGENT_RESULT===`, not after
4. **Agent checkpoint**: Every 10 turns, Agents output a progress checkpoint to track accumulation: `[CHECKPOINT] turn:{N} findings:{count} files_read:{count} remaining_dims:{list}`

## Truncation Detection

Output is considered truncated when the `===AGENT_RESULT_END===` termination marker is missing.

## Recovery Process

- **Rule 1 (Mild, agent_id exists)**: Preserve completed findings (up to last complete `[FNNN]`). Mark the Agent's dimensions with ⚠️. Remaining dimensions are supplemented in the next round.
- **Rule 2 (Severe, agent_id missing)**: Discard all output. Mark the Agent's dimensions with ⚠️. Retry with reduced scope (halve dimensions + halve max_turns, max 5 findings per retry). If retry also truncates, do not retry again — fill gaps in next round or via emergency Agent.

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
