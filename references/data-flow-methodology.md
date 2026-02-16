# Data Flow Analysis Methodology

> Source → [No Sanitization] → Sink = Injection Vulnerability
> Applicable to: code security auditing across all languages. For language-specific Source/Sink lists, see languages/*.md.

---

## Core Formula

```
Injection Vulnerability = Source → [No Sanitization] → Sink
```

User-controllable input reaches a dangerous function with no effective sanitization along the way = vulnerability.

## Three Elements of Taint Analysis

| Element | Description |
|---------|-------------|
| Source (Taint Origin) | User-controllable input (HTTP parameters, headers, cookies, request body, file uploads, path parameters, database data) |
| Propagation | Data flow path (assignment, concatenation, function return, collection storage, object properties, database storage) |
| Sink (Convergence Point) | Dangerous operation point (SQL execution, command execution, file operations, HTTP requests, HTML output, deserialization) |

## Sink Classification Overview

| Sink Type | Vulnerability | CWE | Risk Level |
|-----------|--------------|-----|------------|
| SQL Execution | SQL Injection | 89 | Critical |
| Command Execution | Command Injection | 78 | Critical |
| Deserialization | RCE | 502 | Critical |
| Expression Engine | RCE | 917 | Critical |
| XML Parsing | XXE | 611 | High |
| File Operations | Path Traversal | 22 | High |
| HTTP Requests | SSRF | 918 | High |
| HTML Output | XSS | 79 | Medium |
| URL Redirect | Open Redirect | 601 | Medium |

## Tracing Methods

1. **Backward tracing from Sink**: Sink function ← parameter source ← ... ← Source
2. **Forward tracing from Source**: Source → variable assignment → ... → Sink function
3. **Check sanitization along the propagation path**: Effective sanitization → safe; No sanitization/bypassable → vulnerability

## Effective Sanitization vs Bypassable Sanitization per Sink Type

| Sink Type | Effective Sanitization | Ineffective/Bypassable |
|-----------|----------------------|------------------------|
| SQL | Parameterized queries, ORM parameterized methods | Blacklist filtering, escaping single quotes, addslashes |
| Command | Whitelist + argument array (no shell=True) | Blacklist filtering of special characters |
| File | Whitelist directory + realpath normalization then prefix check | Only filtering ../ |
| HTTP | Domain whitelist + parsed IP check + DNS rebinding protection | Only filtering internal IPs |
| HTML | Context-aware encoding (separate encoding for HTML/JS/CSS/URL) | Only filtering `<script>` |
| Deserialization | Type whitelist | No effective generic sanitization |
| XML | Disable external entities + disable DTD | Only filtering DOCTYPE |

## Audit Process

```
B1. Source Identification → B2. Sink Identification → B3. Taint Propagation Tracing → B4. Sanitization Verification
```

For each Sink, trace parameters backward to determine if they originate from a Source, and check whether effective sanitization exists along the propagation path.
