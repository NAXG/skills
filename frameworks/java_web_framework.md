# Java Web Framework Security Cheat Sheet

> Version scope: Spring MVC, Shiro, Servlet/JSP, Struts | Load condition: Supplement to spring.md, covers Shiro/Servlet-specific issues

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Shiro filterChain anon too broad | Authentication bypass | `download/upload` configured as anon |
| Shiro rememberMe hardcoded key | Deserialization RCE | `setCipherKey(Base64.decode(...))` |
| @PathVariable used directly for DB/file | Injection/traversal | `tableName`/`fileName` not validated |
| Auto parameter binding for file operations | Path traversal | `String fileName` directly concatenated to path |
| Response header injection | Header injection | `setHeader("...", fileName)` concatenation |
| ${params.dataScope} | SQL injection | AOP aspect SQL concatenation |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `@PathVariable String tableName` -> SQL | SQL/command injection | No whitelist validation |
| `Global.getDownloadPath() + fileName` | Path traversal | Direct concatenation |
| `response.setHeader("...", "..." + fileName)` | Header injection | Response header concatenation |
| `filterChainDefinitionMap.put(path, "anon")` | Authentication bypass | Sensitive path set to anonymous |
| `setCipherKey(Base64.decode("..."))` | Deserialization RCE | Shiro hardcoded key |
| `${params.dataScope}` (MyBatis XML) | SQL injection | AOP aspect concatenation |

## Grep Search Patterns

```
# Shiro configuration
filterChainDefinitionMap\.put.*anon
setCipherKey|rememberMe.*cipherKey|Base64\.decode

# PathVariable injection
@PathVariable.*String.*tableName|@PathVariable.*String.*fileName

# File operations
getDownloadPath.*\+.*fileName|writeBytes.*fileName
setHeader.*\+.*fileName|addHeader.*\+.*userInput

# DataScope SQL injection
@DataScope|\$\{params\.dataScope\}|dataScope

# Controller scanning
@.*Mapping|@RequestMapping|@GetMapping|@PostMapping
```

## Audit Checklist

- [ ] Shiro filterChain anon configuration scope
- [ ] Shiro rememberMe key hardcoded
- [ ] @PathVariable used directly for database/file operations
- [ ] File download interface path concatenation
- [ ] Response header concatenation with user input
- [ ] @DataScope / AOP aspect SQL concatenation
- [ ] Spring Boot auto-configuration security defaults
- [ ] AOP aspect execution order
