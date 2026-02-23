# Java Security Audit

> Java security audit main module | See references/agent-contract.md for methodology

## Sub-modules

| Module | Purpose | Load Condition |
|--------|---------|----------------|
| **java.md** (this file) | Source/Sink/Grep patterns/Checklist | Always loaded |
| **java-advanced.md** | Deserialization/JNDI/XXE/Script engines/Fastjson/Practical patterns | When related dependencies or code patterns detected |

---

## Sources (User Input Points)

| Category | API |
|----------|-----|
| HTTP Parameters | `request.getParameter()`, `@RequestParam`, `@PathVariable` |
| Request Body | `@RequestBody`, `request.getInputStream()` |
| HTTP Headers | `request.getHeader()`, `@RequestHeader`, `@CookieValue` |
| File Uploads | `MultipartFile.getOriginalFilename()`, `MultipartFile.getInputStream()` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| SQL Execution | SQL Injection | 89 | `Statement.execute`, MyBatis `${}` |
| Command Execution | Command Injection | 78 | `Runtime.exec`, `ProcessBuilder` |
| Deserialization | RCE | 502 | `readObject`, `JSON.parse`, `Yaml.load` |
| XML Parsing | XXE | 611 | `DocumentBuilder.parse`, `SAXParser.parse` |
| HTTP Requests | SSRF | 918 | `RestTemplate`, `HttpClient`, `OkHttpClient` |
| File Operations | Path Traversal | 22 | `new File()`, `FileInputStream`, `Paths.get` |
| Expression Engines | RCE | 917 | `SpelExpressionParser`, `MVEL.eval`, `OgnlUtil` |
| HTML Output | XSS | 79 | `response.getWriter().write` |
| JNDI | RCE | 74 | `InitialContext.lookup()` |

## Dangerous Dependencies Quick Reference

| Dependency | Dangerous Versions | Exploitation Method |
|------------|-------------------|---------------------|
| commons-collections | 3.1-3.2.1, 4.0 | CC1-CC7 Gadgets |
| commons-beanutils | 1.8.3-1.9.4 | CB1 Gadget |
| fastjson | < 1.2.83 | @type RCE |
| xstream | < 1.4.18 | XML RCE |
| log4j2 | < 2.17.0 | JNDI RCE (CVE-2021-44228) |
| jackson | enableDefaultTyping | Deserialization RCE |
| commons-text | 1.5-1.9 | Text4Shell (CVE-2022-42889) |
| snakeyaml | < 2.0 | Constructor RCE |
| shiro | < 1.7.1 | Authentication bypass |

---

## Grep Search Patterns

```regex
# Deserialization
ObjectInputStream|readObject|readUnshared|XMLDecoder|XStream|fromXML
JSON\.parse|JSON\.parseObject|Yaml\.load

# JNDI injection
\.lookup\s*\(|InitialContext|JdbcRowSetImpl|\$\{jndi:
iiop://|iiopname:|corbaname:|corbaloc:

# XXE
DocumentBuilder|SAXParser|SAXReader|SAXBuilder|XMLInputFactory|TransformerFactory
disallow-doctype-decl|external-general-entities

# SQL injection
\$\{                                          # MyBatis ${} (search in .xml files)
createQuery\s*\(.*\+|createNativeQuery.*\+    # HQL/SQL concatenation
db\.Raw\(.*\+|\.last\s*\(                     # ORM raw SQL
QueryWrapper.*apply|UpdateWrapper.*apply       # MyBatis-Plus
@Query.*nativeQuery.*true                      # Spring Data JPA
fmt\.Sprintf.*(SELECT|INSERT|UPDATE|DELETE)

# Command execution
Runtime\.getRuntime|ProcessBuilder|\.exec\s*\(

# SSRF
new URL|openConnection|HttpClient|OkHttpClient|RestTemplate|WebClient

# File operations
new File\(|FileInputStream|FileOutputStream|Paths\.get
getCanonicalPath|contains.*\.\.|normalize.*path

# Expression/template injection
SpelExpressionParser|parseExpression|MVEL\.eval|OgnlUtil
Velocity\.evaluate|FreeMarker|StringSubstitutor

# Reflection calls
method\.invoke|getDeclaredMethod|getMethod
Class\.forName|ClassLoader\.loadClass
ApplicationContext\.getBean.*String

# XSS filter completeness
class.*Wrapper.*HttpServletRequest
th:utext|th:text

# Configuration security
password.*:|secret.*:|jwt\.secret|api\.key
druid.*stat-view|actuator|management\.endpoints
useSSL.*false|verifyServerCertificate.*false

# Authorization checks
@PreAuthorize|@Secured|@RequiresPermissions
@DeleteMapping|@PutMapping|@PostMapping

# Race conditions
@Transactional|@Lock|FOR UPDATE
balance\s*>=|new HashMap\(|new ArrayList\(
```

---

## Audit Checklist

### High Risk (Must Check)
- [ ] Deserialization entry points (readObject/parseObject/fromXML/Yaml.load)
- [ ] JNDI lookup with controllable parameters
- [ ] XML parsing without disabled external entities (must have disallow-doctype-decl=true)
- [ ] Fastjson version < 1.2.83 or safeMode not enabled
- [ ] Log4j2 version < 2.17.0
- [ ] SQL using MyBatis `${}` or Statement concatenation
- [ ] File download/upload interface path traversal protection
- [ ] Command execution with controllable parameters

### Medium Risk
- [ ] URL parameter controllable (SSRF)
- [ ] Expression/template engine with controllable input (SpEL/OGNL/Velocity)
- [ ] Spring Actuator endpoint exposure
- [ ] Reflection call with controllable parameters (method.invoke)
- [ ] XSS filter completeness — all methods properly overridden

### Authorization Focus
- [ ] Compare @PreAuthorize configuration consistency across CRUD methods in same module
- [ ] Check if DELETE/export/download has permission annotations
- [ ] Verify Service layer resource ownership checks (ownerId)

### Configuration Check
- [ ] application.yml hardcoded keys/weak passwords
- [ ] Overly permissive CORS configuration
- [ ] CSRF protection disabled
- [ ] Debug mode not turned off
- [ ] Database monitoring panel exposed without authentication

### Race Conditions
- [ ] Financial operations have @Lock or SELECT FOR UPDATE
- [ ] @Service singletons with shared mutable state
- [ ] Database unique constraints + exception handling vs application-level checks

---

## PHP Specific Dangerous Patterns (Java Comparison)

| Java Pattern | Description |
|-------------|-------------|
| MyBatis `${}` vs `#{}` | `${}` is string concatenation, `#{}` is parameterized |
| `@DataScope` annotation | AOP aspect may contain SQL concatenation |
| `th:utext` vs `th:text` | In Thymeleaf, utext does not escape |
| `{!! !!}` (Blade) | Equivalent to Java's utext |
| Spring `@Value("${url}")` | Configuration-driven indirect SSRF |
