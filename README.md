# code-audit

[中文文档](README_CN.md)

White-box code security audit skill for Claude Code. Finds real vulnerabilities through source-to-sink data flow tracing — not just pattern matching.

Inspired by [3stoneBrother/code-audit](https://github.com/3stoneBrother/code-audit). The original project carried heavy documentation that largely duplicated knowledge already embedded in LLMs. This fork takes a lightweight approach — structural guidance, execution control, and domain-specific patterns only.

## Quick Start

```bash
# Install
claude skill add gh:NAXG/skills --skill code-audit

# Run
/code-audit standard      # Full OWASP audit
/code-audit deep          # Critical systems, multi-round
```

### Example

```
User: /code-audit deep

Claude: [MODE] deep
        [RECON] 326 files, Django 4.2 + DRF + PostgreSQL + Celery
        [PLAN] 4 Agents, D1-D10 coverage, estimated 90 turns
        ... (user confirms) ...
        [REPORT] 3 Critical, 7 High, 5 Medium, 2 Low
```

## Requirements

- **Python 3** (required)
- **semgrep** (required)

## What It Covers

### 9 Languages, 13 Frameworks

| Languages | Frameworks |
|-----------|------------|
| Java | Spring, MyBatis |
| Python | Django, Flask, FastAPI |
| Go | Gin |
| JavaScript/TypeScript | Express, Koa, NestJS/Fastify |
| PHP | Laravel |
| Ruby | Rails |
| C# / .NET | ASP.NET Core |
| C/C++ | — |
| Rust | Actix-web, Axum, Rocket |

### 10 Security Dimensions

| # | Dimension | Track | What It Finds |
|---|-----------|-------|---------------|
| D1 | Injection | Sink-driven | SQLi, CMDi, LDAP, SSTI, SpEL, XSS, NoSQL |
| D2 | Authentication | Config-driven | Token/session flaws, weak passwords, bypass |
| D3 | Authorization | Control-driven | IDOR, privilege escalation, missing access control |
| D4 | Deserialization | Sink-driven | Java/Python/PHP gadget chains, XXE |
| D5 | File Operations | Sink-driven | Upload, path traversal, Zip Slip |
| D6 | SSRF | Sink-driven | URL injection, DNS rebinding |
| D7 | Cryptography | Config-driven | Hardcoded keys, weak algorithms, IV reuse |
| D8 | Configuration | Config-driven | Debug exposure, CORS, error leaks |
| D9 | Business Logic | Control-driven | Race conditions, workflow bypass, mass assignment |
| D10 | Supply Chain | Config-driven | Dependency CVEs, outdated libraries |

### 12 Security Domain Modules

SQL Injection, Command Injection, XSS, Authentication, Authorization, File Operations, SSRF, Deserialization, API Security, LLM/AI Security, Race Conditions, Cryptography.

## Architecture

### Audit Modes

| Mode | Rounds | Phases | Agents |
|------|--------|--------|--------|
| `standard` | 1–2 | Recon → Hunt → Merge → Deep Dive → Validation → Report | By scale |
| `deep` | 2–3 | Full pipeline, multi-round with convergence control | By scale |

### Multi-Agent Workflow

```
Phase 1: Recon
  ├─ Tech stack identification
  ├─ Attack surface mapping
  └─ Entry point inventory

Phase 2: Hunt (parallel agents)
  ├─ Semgrep baseline scan (standard/deep)
  ├─ Agent 1: Injection (D1)           [sink-driven]
  ├─ Agent 2: Auth + AuthZ (D2+D3+D9) [control-driven]
  ├─ Agent 3: File + SSRF (D5+D6)     [sink-driven]
  └─ Agent N: ...                      [by project scale]

Phase 2.5: Merge
  ├─ Output collection & format validation
  └─ Pre-validation statistics

Phase 3: Deep Dive (standard/deep)
  ├─ Incomplete data flow completion
  └─ Cross-agent attack chain synthesis

Phase 4: Validation (standard/deep)
  ├─ Semgrep cross-validation
  ├─ Multi-agent cross-validation
  └─ Severity calibration

Phase 5: Report
  └─ Structured output with evidence & PoCs
```

### Source → Propagation → Sink

Every vulnerability is traced through the same model:

1. **Source** — where attacker-controlled data enters
2. **Propagation** — whether filtering/transformation is effective
3. **Sink** — whether the dangerous operation is reachable

### Anti-Hallucination

- File paths must be verified with Glob/Read before reporting
- Code snippets must come from actual Read tool output
- No fabricated paths, no guessed code
- **Core principle: better to miss a vulnerability than report a false positive**

## Report Output

| Section | standard | deep |
|---------|:--------:|:----:|
| Executive Summary | ✓ | ✓ |
| Finding Statistics | ✓ | ✓ |
| Coverage Matrix (D1–D10) | ✓ | ✓ |
| Vulnerability Details + PoC | ✓ | ✓ |
| Audit Limitations | ✓ | ✓ |
| Semgrep Verification Evidence | ✓ | ✓ |
| Attack Chain Analysis | ✓ | ✓ |
| Attack Path Scoring | ✓ | ✓ |

## Project Structure

```
code-audit/
├── SKILL.md                     # Skill entry point
├── scripts/
│   └── parse_semgrep_baseline.py
├── references/          (12)    # Execution control & methodology
├── languages/            (9)    # Language-specific audit patterns
├── frameworks/          (13)    # Framework-specific audit patterns
└── domains/             (12)    # Security domain modules
```

## License

MIT

## Limitations

### Knowledge Cutoff

This skill relies on LLM analysis. Current models have knowledge cutoff around **June 2025**.

- **Supply Chain (D10)** coverage may be incomplete for CVEs published after this date
- Recommendation: Use external tools alongside this audit:
  - `semgrep` — SAST baseline scanning
  - `osv-scanner` — Dependency vulnerability detection

### Computational Constraints

LLM-based analysis is bounded by context window and inference budget. For large codebases, coverage may be incomplete — certain files or data flows could be missed. Treat results as a supplement to, not a replacement for, comprehensive manual review.

### Tool Integration

This skill focuses on **Source-to-Sink data flow tracing**. External scanners complement but do not replace manual analysis for:
- Business logic vulnerabilities
- Complex authentication/authorization flaws
- Multi-step attack chains

## Disclaimer

This skill is intended for **authorized security testing** only. Users must have legal authorization to audit the target code and comply with applicable laws. Unauthorized security testing of systems you do not own may be illegal.
