---
name: code-audit
description: "White-box code security audit — finds vulnerabilities (SQLi, XSS, RCE, SSRF, IDOR, deserialization, etc.), reviews authentication/authorization, traces Source-to-Sink data flows, and checks OWASP Top 10 coverage. Use when asked to find vulnerabilities, do security review, penetration-test prep, or audit code for security issues. Modes: quick (fast scan), standard (full OWASP), deep (multi-round with attack chains)."
argument-hint: "[mode] — modes: quick|standard|deep"
allowed-tools: Read, Grep, Glob, Bash, Task, Write
recommended-model: "opus"
---

# code-audit Skill

> White-box Code Security Audit System
>
> **Version**: 5.2.0 | **Updated**: 2026-02-17
>
> **System Requirements**: Python 3 (required), semgrep (required for standard/deep modes; quick mode can proceed without it)
>
> **Mindset: Attacker's perspective.** During the audit, assume every line of code is exploitable until proven otherwise. Don't "defend the developer" — instead, "find paths for the attacker."

---

## I. Core Principles (Always in Effect)

### 1.1 Anti-Hallucination Hard Rules

- Do not guess file paths: must verify file existence with `Glob/Read`
- Do not fabricate code snippets: must reference actual output from the `Read` tool
- Do not report vulnerabilities in unread files: code that hasn't been read must not appear in the report

**Core principle: Better to miss a vulnerability than to report a false positive.**

### 1.2 Anti-Confirmation Bias Rules

- Do not skip a vulnerability category just because it "seems unlikely"
- Must enumerate sensitive operations and verify each one
- Must complete the full checklist, treating all dimensions equally

### 1.3 Unified Analysis Model (Source → Propagation → Sink)

All vulnerabilities are assessed using the following flow:
1. Find the Source (attack surface)
2. Trace the Propagation (is filtering/transformation effective?)
3. Check the Sink (is the dangerous operation reachable?)

### 1.4 Priority Principle

```
Priority = (Attack Surface Size × Potential Impact) / Exploitation Complexity
```

**Top priority: Authentication chain** (authentication bypass amplifies the severity of other vulnerabilities).

---

## II. Scan Modes

| Mode | Use Case | Rounds | Phase Sequence | Recon Gate | Agent Count | Coverage Threshold | D1-D3 Requirement | Report |
|------|----------|--------|----------------|------------|-------------|--------------------|--------------------|--------|
| `quick` | CI/CD, small projects | 1 | 1→2→5 | quick_passed | 1-3 | ≥8/10 | Not enforced | Compact |
| `standard` | Regular audit | 1-2 | 1→2→2.5→3→4→5 | all_passed | By scale | ≥8/10 | All ✅ | Full |
| `deep` | Critical systems | 2-3 | 1→2→2.5→3→4→5 (multi-round) | all_passed | By scale | ≥9/10 | All ✅ | Full |

### Mandatory Loading by Mode

| Mode | Required Documents |
|------|-------------------|
| `quick` | execution-controller.md + agent-contract.md + phase0-attack-surface.md |
| `standard` | quick baseline + references/coverage-matrix.md |
| `deep` | standard baseline + references/agent-output-recovery.md |

For execution flow, gates, phase transitions, report admission, and other rules, see [execution-controller.md](references/execution-controller.md) (authoritative source for execution flow; in case of conflict with other documents, this file takes precedence).

---

## III. Reference Index

### 3.1 Execution Control

| Document | Responsibility | Required for Mode |
|----------|---------------|-------------------|
| [execution-controller.md](references/execution-controller.md) | Execution order, gates, phase transitions, `can_report()`, budget strategy, cross-round protocol, Deep mode state machine | All modes |

### 3.2 Coverage & Validation

| Document | Responsibility | Required for Mode |
|----------|---------------|-------------------|
| [coverage-matrix.md](references/coverage-matrix.md) | D1-D10 dimension checklist + track-based coverage assessment + EPR calculation | standard/deep |
| [validation-and-severity.md](references/validation-and-severity.md) | Four-step vulnerability validation, severity calibration | All modes |

### 3.3 Agent & Output

| Document | Responsibility | Required for Mode |
|----------|---------------|-------------------|
| [agent-contract.md](references/agent-contract.md) | Agent contract, output templates, truncation handling | All modes |
| [agent-output-recovery.md](references/agent-output-recovery.md) | Truncation detection and recovery process | deep |
| [report-template.md](references/report-template.md) | Report template, gate evidence, deduplication rules | All modes |

### 3.4 Reconnaissance & Pattern Library

| Document | Responsibility | Required for Mode |
|----------|---------------|-------------------|
| [phase0-attack-surface.md](references/phase0-attack-surface.md) | Phase 0 attack surface mapping | All modes |
| [pattern-library-routing.md](references/pattern-library-routing.md) | Language/framework/domain module loading routing | All modes |
| [semgrep-playbook.md](references/semgrep-playbook.md) | Semgrep execution flow | All modes |
| [data-flow-methodology.md](references/data-flow-methodology.md) | Source→Sink data flow methodology | All modes (referenced by language modules) |

### 3.5 Framework Modules

| Framework | Document |
|-----------|----------|
| Spring | [frameworks/spring.md](frameworks/spring.md) |
| MyBatis | [frameworks/mybatis_security.md](frameworks/mybatis_security.md) |
| Django | [frameworks/django.md](frameworks/django.md) |
| Flask | [frameworks/flask.md](frameworks/flask.md) |
| FastAPI | [frameworks/fastapi.md](frameworks/fastapi.md) |
| Gin | [frameworks/gin.md](frameworks/gin.md) |
| Express | [frameworks/express.md](frameworks/express.md) |
| Koa | [frameworks/koa.md](frameworks/koa.md) |
| NestJS/Fastify | [frameworks/nest_fastify.md](frameworks/nest_fastify.md) |
| Laravel | [frameworks/laravel.md](frameworks/laravel.md) |
| Rails | [frameworks/rails.md](frameworks/rails.md) |
| ASP.NET Core | [frameworks/dotnet.md](frameworks/dotnet.md) |
| Rust Web | [frameworks/rust_web.md](frameworks/rust_web.md) |

For routing rules, see [pattern-library-routing.md](references/pattern-library-routing.md).

### 3.6 Language Modules

| Language | Main Document | Advanced Module |
|----------|--------------|-----------------|
| Java | [java.md](languages/java.md) | [java-advanced.md](languages/java-advanced.md) (deep mode or when deserialization/JNDI/XXE detected) |
| Python | [python.md](languages/python.md) | - |
| PHP | [php.md](languages/php.md) | - |
| Go | [go.md](languages/go.md) | - |
| JavaScript | [javascript.md](languages/javascript.md) | - |
| C#/.NET | [dotnet.md](languages/dotnet.md) | - |
| C/C++ | [c_cpp.md](languages/c_cpp.md) | - |
| Ruby | [ruby.md](languages/ruby.md) | - |
| Rust | [rust.md](languages/rust.md) | - |

### 3.7 Security Domain Modules

| Domain | Document | Loading Condition |
|--------|----------|-------------------|
| SQL Injection | [sql-injection.md](domains/sql-injection.md) | Database dependency or SQL Sink |
| Command Injection | [command-injection.md](domains/command-injection.md) | exec/system/popen Sink |
| XSS | [xss.md](domains/xss.md) | Web frontend rendering or template engine |
| Authentication | [authentication.md](domains/authentication.md) | Login/registration/password functionality |
| Authorization | [authorization.md](domains/authorization.md) | Roles/permissions/access control |
| File Operations | [file-operations.md](domains/file-operations.md) | File upload/download/read-write |
| SSRF | [ssrf.md](domains/ssrf.md) | Server-side HTTP requests |
| Deserialization | [deserialization.md](domains/deserialization.md) | Deserialization Sink |
| API Security | [api-security.md](domains/api-security.md) | REST/GraphQL/gRPC API |
| LLM/AI | [llm-security.md](domains/llm-security.md) | LLM/AI/ML integration |
| Race Conditions | [race-conditions.md](domains/race-conditions.md) | Concurrent operation scenarios |
| Cryptography | [cryptography.md](domains/cryptography.md) | Encryption/JWT/signing operations |
