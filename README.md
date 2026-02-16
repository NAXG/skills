# code-audit

[中文文档](README_CN.md)

White-box code security audit skill for Claude Code. Finds real vulnerabilities through source-to-sink data flow tracing — not just pattern matching.

Inspired by [3stoneBrother/code-audit](https://github.com/3stoneBrother/code-audit). The original project carried heavy documentation that largely duplicated knowledge already embedded in LLMs. This fork takes a lightweight approach — structural guidance, execution control, and domain-specific patterns only.

## Quick Start

```bash
# Install
claude skill add gh:NAXG/skills --skill code-audit

# Run
/code-audit quick         # CI/CD, small projects
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
- **semgrep** (recommended — the audit proceeds without it)

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
| `quick` | 1 | Recon → Hunt → Report | 1–3 |
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
  ├─ Output collection & deduplication
  └─ Pre-validation statistics

Phase 3: Deep Dive (standard/deep)
  ├─ Cross-agent attack chain synthesis
  └─ Deeper data flow analysis

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

| Section | quick | standard | deep |
|---------|:-----:|:--------:|:----:|
| Executive Summary | ✓ | ✓ | ✓ |
| Finding Statistics | ✓ | ✓ | ✓ |
| Coverage Matrix (D1–D10) | ✓ | ✓ | ✓ |
| Vulnerability Details + PoC | ✓ | ✓ | ✓ |
| Audit Limitations | ✓ | ✓ | ✓ |
| Execution Gate Evidence | | ✓ | ✓ |
| Attack Chain Analysis | | ✓ | ✓ |
| Attack Path Scoring | | ✓ | ✓ |
| Attack Timeline Simulation | | | ✓ |

## Project Structure

```
code-audit/
├── SKILL.md                     # Skill entry point
├── scripts/
│   └── parse_semgrep_baseline.py
├── references/          (10)    # Execution control & methodology
├── languages/            (9)    # Language-specific audit patterns
├── frameworks/          (13)    # Framework-specific audit patterns
└── domains/             (12)    # Security domain modules
```

## License

MIT

## Disclaimer

This skill is intended for **authorized security testing** only. Users must have legal authorization to audit the target code and comply with applicable laws. Unauthorized security testing of systems you do not own may be illegal.
