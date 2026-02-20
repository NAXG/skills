# Semgrep Playbook

> **DEPRECATED**: This file's content has been integrated into [execution-controller.md](execution-controller.md) §Semgrep Execution Timing. This file is retained for reference only and is no longer loaded during execution.

> This file must be loaded during Phase 2 Step 0 (Semgrep baseline scan).
> Validation is performed uniformly in Phase 4.

## Execution Prerequisites (Mandatory)

- Execute only after [Execution Controller](execution-controller.md) Step 4 gate check passes
- **Quick mode does not execute Semgrep scan**, Agents start directly (quick skips Phase 3/4, Semgrep results have no consumer)
- Gate field determination and failure handling are defined in `execution-controller.md`; this file does not redefine them

## Fault Tolerance Rules

Semgrep is **mandatory** in standard/deep modes. When issues occur, follow this process:

1. Check if semgrep is available: `which semgrep` or `semgrep --version`
2. If unavailable: trigger [HALT] — prompt user to install semgrep before continuing
3. If execution times out (>5 minutes): retry once. If still failing, trigger [HALT]
4. If execution errors but has partial output: attempt to parse existing output, set `semgrep_status=partial` (acceptable, audit continues)

Quick mode does not execute Semgrep (quick skips Phase 3/4, Semgrep results have no consumer).
- Does not affect coverage assessment

## Baseline Command

```bash
semgrep scan --config auto --json --output semgrep-baseline.json
```

Script location:
- `parse_semgrep_baseline.py` is located in the `scripts/` directory of this skill, invoked via relative path.

## Parse Command (semgrep-baseline.json raw file is too large, script parsing required)

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json \
  --min-severity WARNING \
  --exclude-third-party \
  --format json \
  --output semgrep-findings.json
```


## Parameter Reference (parse_semgrep_baseline.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input` | `semgrep-baseline.json` | Input Semgrep JSON file (positional argument). |
| `--min-severity {INFO\|WARNING\|ERROR}` | `INFO` | Only keep findings at or above the specified severity. |
| `--format {text\|json}` | `text` | Output format. `json` outputs findings with `finding_id`; `text` includes summary and details. |
| `--output <path>` | `-` | Output file path, `-` for stdout. |
| `--top <n>` | `10` | Number of Top rules/files in `text` mode summary. |
| `--max-message-length <n>` | `140` | Message truncation length in text mode. |
| `--no-dedupe` | `false` | Disable deduplication. |
| `--include-path-regex <regex>` | empty | Only keep path-matching items, can be passed multiple times. |
| `--exclude-path-regex <regex>` | empty | Exclude path-matching items, can be passed multiple times. |
| `--include-rule-regex <regex>` | empty | Only keep rule ID-matching items, can be passed multiple times. |
| `--exclude-rule-regex <regex>` | empty | Exclude rule ID-matching items, can be passed multiple times. |
| `--exclude-third-party` | `false` | Exclude common third-party directories and `*.min.js/css`. |

## Common Filter Combinations

1. `WARNING + ERROR`:

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json --min-severity WARNING
```

2. `ERROR` only:

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json --min-severity ERROR
```

3. Focus on backend Java:

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json \
  --min-severity WARNING \
  --include-path-regex 'src/main/java/' \
  --exclude-path-regex '/src/main/webapp/'
```

4. Focus on injection/XSS:

```bash
python3 scripts/parse_semgrep_baseline.py semgrep-baseline.json \
  --min-severity WARNING \
  --include-rule-regex '(xss|injection|sql|command)'
```
