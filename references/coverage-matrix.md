# 10-Dimension Coverage Matrix

> Load after Phase 2 completion. Used to verify coverage completeness; does not drive the audit.

## Usage

After Phase 2 completion, check coverage status for each dimension against this matrix:
- ✅ Covered — In-depth analysis performed (code reading + data flow tracing)
- ⚠️ Shallow coverage — Only Grep-searched, not deeply verified
- ❌ Not covered — Not addressed at all
- N/A Not applicable — This dimension does not apply to the current project

**Termination condition: Coverage ≥ 8/(10-N/A count) and D1-D3 all ✅ before entering the report phase.**

---

## N/A Determination Rules

### Determination Conditions

Marking a dimension as N/A requires **all** of:
1. Reconnaissance did not detect key Sink categories for that dimension
2. Agent Grep searches returned zero hits (at least 3 **distinct** related pattern searches with no results)
3. The Grep patterns used must cover at least 2 different Sink sub-categories for that dimension (e.g., for D6/SSRF: both HTTP client calls AND webhook/callback patterns)
4. N/A determination must be documented with the specific Grep patterns tried and their results

### Constraints

These restrictions reflect the reality that certain vulnerability categories are nearly universal in web applications. Allowing them to be skipped via N/A would create dangerous blind spots.

- **D1 (Injection) does not allow N/A**: Almost every application processes user input in some form — even non-web projects may have CLI arguments, config files, or inter-process communication that could be injection vectors
- **D2 (Authentication) and D3 (Authorization)**: N/A only allowed for library projects (no HTTP entry points); not allowed for web applications — any web application that serves users must authenticate and authorize them, even if it delegates to an external identity provider
- D4-D10: May be marked N/A when determination conditions are met

### Overall Scoring Formula

```text
Coverage = ✅ count / (10 - N/A count)
```

> Dimension assessment: a dimension is marked ✅ only when all Tracks within that dimension meet the ✅ standard. If any Track is ⚠️ or ❌, the dimension is downgraded.

---

## D1: Injection

**Key question:** Can user input reach SQL/Cmd/LDAP/SSTI/SpEL/ORM execution points?

Checklist:
- [ ] SQL Injection — String-concatenated SQL, dynamic query building, ORM raw queries
- [ ] Command Injection — Do system command execution functions accept user input?
- [ ] LDAP Injection — Do LDAP queries use unfiltered input?
- [ ] Template Injection (SSTI) — Does the template engine render user-controlled strings?
- [ ] Expression Injection (SpEL/OGNL/EL) — Does expression evaluation use user input?
- [ ] NoSQL Injection — Do MongoDB/Redis queries use unvalidated input?
- [ ] XPath/XML Injection — Do XML queries/parsing use user input?
- [ ] XSS (Reflected) — Is user input written directly to HTTP response/HTML without encoding?
- [ ] XSS (Stored) — Is stored user data encoded when displayed?
- [ ] XSS (DOM-based) — Does frontend JavaScript insert user input into the DOM (innerHTML/document.write, etc.)?

**Depth standard:** Trace at least 3 complete Source→Sink data flow paths.

---

## D2: Authentication

**Key question:** Are token generation, validation, and expiration complete? Can authentication be bypassed?

Checklist:
- [ ] Token/Session Generation — Uses secure random numbers? Sufficient entropy?
- [ ] Token Validation — Is the signature verified? Is expiration checked? Is the issuer checked?
- [ ] Password Storage — Uses secure hash algorithms (bcrypt/scrypt/argon2)?
- [ ] Authentication Bypass — Are there whitelisted paths that bypass authentication?
- [ ] Session Management — Session fixation, session hijacking risks
- [ ] Multi-factor Authentication — Can it be bypassed or downgraded?
- [ ] Default Credentials — Are there hardcoded usernames/passwords?

**Depth standard:** Read the complete authentication filter/middleware code; trace the token lifecycle.

---

## D3: Authorization

**Key question:** Does every sensitive operation verify user ownership? Are there horizontal/vertical privilege escalation paths?

Checklist:
- [ ] Horizontal Privilege Escalation (IDOR) — Is ownership verified when accessing another user's resources?
- [ ] Vertical Privilege Escalation — Can regular users access admin interfaces?
- [ ] Permission Annotations/Decorators — Is there actual AOP/middleware implementation?
- [ ] Object-Level Access Control — Do modify/delete operations verify ownership?
- [ ] Function-Level Access Control — Do admin functions have separate permission checks?
- [ ] Batch Operations — Are permissions verified for each ID in batch operations?

**Depth standard:** Verify complete authorization chains for at least 5 sensitive endpoints.

---

## D4: Insecure Deserialization

**Key question:** Does untrusted data undergo deserialization?

Checklist:
- [ ] Native Deserialization — Java readObject / Python pickle / PHP unserialize
- [ ] JSON Deserialization — Polymorphic type handling (Jackson defaultTyping, Fastjson autoType)
- [ ] XML Deserialization — XXE attacks, XStream deserialization
- [ ] Custom Protocols — Custom serialization/deserialization implementations
- [ ] Class Loading — Can dynamic class loading be exploited?

**Depth standard:** Confirm whether deserialization entry points accept external input; check type whitelists/blacklists.

---

## D5: File Operations

**Key question:** Are upload/download paths controllable? Is path traversal possible?

Checklist:
- [ ] File Upload — File type validation, storage path control, filename handling
- [ ] File Download — Can path parameters be manipulated (../)?
- [ ] Path Traversal — Does file path concatenation use user input?
- [ ] File Inclusion — Does dynamic file inclusion use user input (PHP include)?
- [ ] Temporary Files — Is temporary file creation secure (permissions, naming)?
- [ ] ZIP Extraction — Is Zip Slip attack defended against?

**Depth standard:** Trace the complete path of filename/path parameters from request to filesystem operations.

---

## D6: SSRF (Server-Side Request Forgery)

**Key question:** Is the URL of server-side HTTP requests user-controllable?

Checklist:
- [ ] HTTP Client Calls — Are URL parameters from user input?
- [ ] Data Import/Export — Are external URL data sources controllable?
- [ ] JDBC URL — Are database connection strings user-controllable?
- [ ] Image/Resource Fetching — Are avatar/preview image URLs user-controllable?
- [ ] Webhook/Callback — Can callback URLs point to internal networks?
- [ ] DNS Rebinding — Is DNS resolution validated only once?

**Depth standard:** Confirm URL validation logic completeness (protocol whitelist, IP blacklist, DNS rebinding defense).

---

## D7: Cryptographic Failures

**Key question:** Hardcoded keys? Weak algorithms? Insecure key management?

Checklist:
- [ ] Hardcoded Keys/Passwords — Are there plaintext keys in the code?
- [ ] Weak Hash Algorithms — MD5/SHA1 used for password hashing
- [ ] Weak Encryption Algorithms — DES/3DES/RC4 and other deprecated algorithms
- [ ] ECB Mode — AES-ECB mode usage
- [ ] IV/Nonce Reuse — Is the initialization vector fixed or predictable?
- [ ] Random Number Quality — Is Math.random()/rand() used to generate security tokens?
- [ ] Certificate Validation — Is HTTPS certificate validation disabled?

**Depth standard:** Trace the complete key lifecycle (generation → storage → usage → rotation).

---

## D8: Security Misconfiguration

**Key question:** Debug interfaces exposed? CORS too permissive? Insecure default configuration?

Checklist:
- [ ] Debug Mode — Is debug enabled in production?
- [ ] Admin Endpoint Exposure — Are Actuator/Admin endpoints publicly accessible?
- [ ] CORS Configuration — Does it allow * origin or reflect Origin?
- [ ] HTTP Headers — Missing security headers (CSP, HSTS, X-Frame-Options)
- [ ] Error Handling — Does it leak stack traces/internal paths?
- [ ] Default Configuration — Do databases/caches/message queues use default credentials?
- [ ] Directory Listing — Is directory structure exposed?

**Depth standard:** Read main configuration files; check production/development configuration differences.

---

## D9: Business Logic Flaws

**Key question:** Race conditions? Skippable workflows? Tamper-able quantities/amounts?

Checklist:
- [ ] Race Conditions — Do critical operations have concurrency protection (TOCTOU)?
- [ ] Workflow Bypass — Can multi-step workflows be skipped?
- [ ] Quantity Tampering — Are order amounts/quantities validated only on the frontend?
- [ ] Replay Attacks — Is there nonce/timestamp anti-replay protection?
- [ ] Mass Assignment — Does object binding restrict modifiable fields?
- [ ] Enumeration Attacks — Can usernames/emails be enumerated?
- [ ] Rate Limiting — Do critical endpoints have rate limits?

**Depth standard:** Trace state transition logic for at least 2 complete business workflows.

---

## D10: Supply Chain Security

**Key question:** Do dependencies have known CVEs? Are untrusted components used?

Checklist:
- [ ] Known CVEs — Do dependency versions have known vulnerabilities?
- [ ] Outdated Dependencies — Are unmaintained libraries in use?
- [ ] Dependency Locking — Is there a lock file pinning versions?
- [ ] Internal Dependencies — Are private package sources secure?
- [ ] Build Security — Do build scripts execute untrusted code?

**Depth standard:** Check critical dependency version numbers against known CVE databases.

---

## Coverage Summary Template

```
| # | Dimension | Status | Findings | Key Notes |
|---|-----------|--------|----------|-----------|
| D1 | Injection | ✅/⚠️/❌ | {n} | |
| D2 | Authentication | ✅/⚠️/❌/N/A | {n} | |
| D3 | Authorization | ✅/⚠️/❌/N/A | {n} | |
| D4 | Deserialization | ✅/⚠️/❌/N/A | {n} | |
| D5 | File Operations | ✅/⚠️/❌/N/A | {n} | |
| D6 | SSRF | ✅/⚠️/❌/N/A | {n} | |
| D7 | Cryptography | ✅/⚠️/❌/N/A | {n} | |
| D8 | Configuration | ✅/⚠️/❌/N/A | {n} | |
| D9 | Business Logic | ✅/⚠️/❌/N/A | {n} | |
| D10 | Supply Chain | ✅/⚠️/❌/N/A | {n} | |
| **Total** | | **{n}/(10-N/A count)** | **{total}** | |
```

**Assessment:**
- Coverage ≥ 8/(10-N/A count) and D1-D3 all ✅ → Report can be generated
- Otherwise → Generate gap list and launch supplemental audit rounds

---

## Track-Based Coverage Assessment

Coverage is assessed by audit strategy tracks to prevent "searched = covered."

### Track Mapping

- Sink-driven: `D1 / D4 / D5 / D6`
- Control-driven: `D3 / D9`
- Config-driven: `D2 / D7 / D8 / D10`

### Sink-driven Assessment

- `✅`: Core Sink categories covered + data flow tracing performed
- `⚠️`: Pattern matches only, no effective tracing performed
- `❌`: Dimension was not audited
- `N/A`: Reconnaissance did not detect related Sinks + Agent Grep searches returned zero hits

### Control-driven Assessment

- `✅`: Endpoint-permission matrix systematically audited, CRUD permission consistency verified
- `⚠️`: Only spot-checked a few endpoints, no systematic verification
- `❌`: No endpoint control audit performed
- `N/A`: Library project, no endpoint control audit needed

```text
Endpoint Audit Rate (EPR) = verified permission endpoint count / total endpoints in endpoint-permission matrix
```

**Data source**: The endpoint-permission matrix is produced during reconnaissance (see recon-attack-surface.md §Endpoint-Permission Matrix). Agents covering D3/D9 must reference this matrix and report:
```text
epr: verified={n} total={n} rate={n%}
crud_types: {n} resource types with CRUD consistency verified
```

- `✅` minimum thresholds:
  - `standard`: `EPR >= 30%` and at least 3 resource types with CRUD permission consistency comparison completed
  - `deep`: `EPR >= 50%` and at least 3 resource types with CRUD permission consistency comparison completed
- Grep pattern only, without systematic enumeration based on endpoint matrix: can only be marked `⚠️` at most

### Config-driven Assessment

- `✅`: Core configuration items, versions/algorithms/policies all checked
- `⚠️`: Incomplete checking
- `❌`: Not checked
- `N/A`: Reconnaissance did not detect related configuration + Agent Grep searches returned zero hits

### Mode Thresholds

| Mode | Coverage Threshold | Additional Conditions |
|------|-------------------|----------------------|
| standard | ≥ 8/(10-N/A count) dimensions ✅ | D1-D3 must all be ✅ |
| deep | ≥ 9/(10-N/A count) dimensions ✅ | D1-D3 must all be ✅ |
