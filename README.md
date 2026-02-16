# code-audit

**Version**: 5.2.0

A structured, multi-phase security audit system that finds real vulnerabilities through source-to-sink data flow tracing — not just pattern matching. Covers OWASP Top 10, authentication/authorization chains, injection flaws, deserialization, SSRF, and more.

Inspired by [3stoneBrother/code-audit](https://github.com/3stoneBrother/code-audit). This project takes a lightweight approach — the original carried extensive documentation that largely duplicated knowledge already embedded in LLMs. We stripped redundant content and kept only the structural guidance, execution control, and domain-specific patterns that actually steer the audit agent toward better results.

## Features

- **10-Dimension Coverage** — Systematically audits Injection, Authentication, Authorization, Deserialization, File Operations, SSRF, Cryptography, Configuration, Business Logic, and Supply Chain
- **Source-to-Sink Tracing** — Tracks user input from entry points through transformations to dangerous operations, eliminating false positives
- **Multi-Agent Architecture** — Parallelizes scanning with specialized agents partitioned by language, framework, or security domain
- **Three Audit Modes** — `quick` for CI/CD, `standard` for regular audits, `deep` for critical systems with multi-round iteration
- **Anti-Hallucination Rules** — Every reported vulnerability must reference actual code read by the tool; no guessed paths or fabricated snippets
- **Semgrep Integration** — Optional baseline scanning with automated result parsing and cross-validation
- **Structured Reporting** — Findings include CVSS scores, data flow diagrams, PoC payloads, attack chain analysis, and attack path scoring

## Supported Languages & Frameworks

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

## Security Domains

Dedicated analysis modules for: SQL Injection, Command Injection, XSS, Authentication, Authorization, File Operations, SSRF, Deserialization, API Security, LLM/AI Security, Race Conditions, and Cryptography.

## Installation

```bash
claude install gh:anthropics/claude-code-skill-code-audit
```

Or manually clone this repository into your Claude Code skills directory.

## Requirements

- **Python 3** (required)
- **semgrep** (recommended — enhances baseline scanning, but the audit proceeds without it)

## Usage

Invoke the skill in Claude Code:

```
/code-audit quick      # Fast scan — CI/CD, small projects
/code-audit standard   # Full OWASP audit with validation
/code-audit deep       # Multi-round audit for critical systems
```

### Audit Modes

| Mode | Use Case | Rounds | Phases | Agent Count |
|------|----------|--------|--------|-------------|
| `quick` | CI/CD, small projects | 1 | Recon → Hunt → Report | 1–3 |
| `standard` | Regular audit | 1–2 | Recon → Hunt → Merge → Deep Dive → Validation → Report | By scale |
| `deep` | Critical systems | 2–3 | Full pipeline, multi-round with attack chains | By scale |

### Audit Phases

1. **Phase 1 — Recon**: Attack surface mapping, tech stack identification, entry point inventory
2. **Phase 2 — Hunt**: Parallel agent scanning across all 10 dimensions
3. **Phase 2.5 — Merge**: Agent output collection, deduplication, pre-validation statistics
4. **Phase 3 — Deep Dive**: Cross-agent attack chain synthesis, deeper data flow analysis
5. **Phase 4 — Validation**: Semgrep cross-validation, multi-agent cross-validation, severity calibration
6. **Phase 5 — Report**: Structured security report with evidence and PoCs

## Report Output

Reports include:

- **Executive Summary** — Project scope, tech stack, coverage statistics
- **Finding Statistics** — Severity breakdown (Critical / High / Medium / Low)
- **Coverage Matrix** — D1–D10 dimension status
- **Vulnerability Details** — File location, data flow, evidence, PoC, impact
- **Attack Chain Analysis** — Multi-step exploitation paths (standard/deep)
- **Attack Path Scoring** — Authentication requirements, complexity, success rate (standard/deep)
- **Audit Limitations** — Uncovered areas, N/A rationale, static analysis constraints

## How It Works

The audit follows an attacker's mindset: *every line of code is exploitable until proven otherwise*.

All vulnerabilities are assessed using the **Source → Propagation → Sink** model:

1. **Find the Source** — identify the attack surface (user inputs, external data)
2. **Trace the Propagation** — check if filtering/transformation is effective
3. **Check the Sink** — determine if the dangerous operation is reachable

Priority is calculated as:

```
Priority = (Attack Surface Size × Potential Impact) / Exploitation Complexity
```

## Project Structure

```
code-audit/
├── SKILL.md                    # Skill definition and entry point
├── scripts/
│   └── parse_semgrep_baseline.py
├── references/                 # Execution control & methodology
│   ├── execution-controller.md
│   ├── agent-contract.md
│   ├── coverage-matrix.md
│   ├── validation-and-severity.md
│   ├── report-template.md
│   ├── data-flow-methodology.md
│   ├── phase0-attack-surface.md
│   ├── pattern-library-routing.md
│   ├── semgrep-playbook.md
│   └── agent-output-recovery.md
├── languages/                  # Language-specific audit patterns
│   ├── java.md, java-advanced.md
│   ├── python.md, javascript.md
│   ├── go.md, php.md, ruby.md
│   ├── c_cpp.md, rust.md
│   └── dotnet.md
├── frameworks/                 # Framework-specific audit patterns
│   ├── spring.md, django.md, flask.md
│   ├── fastapi.md, express.md, koa.md
│   ├── gin.md, laravel.md, rails.md
│   ├── nest_fastify.md, dotnet.md
│   ├── rust_web.md
│   └── mybatis_security.md
└── domains/                    # Security domain modules
    ├── sql-injection.md, xss.md
    ├── command-injection.md
    ├── authentication.md, authorization.md
    ├── file-operations.md, ssrf.md
    ├── deserialization.md
    ├── api-security.md, cryptography.md
    ├── race-conditions.md
    └── llm-security.md
```

## License

MIT
