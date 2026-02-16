# Gin Security Cheat Sheet

> Version scope: Gin 1.x, GORM | Load condition: go.mod contains gin-gonic/gin

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| cors.Default() | CORS wide open | Allows all origins |
| AllowCredentials + AllowOrigins=["*"] | Credential theft | Dangerous combination |
| SetTrustedProxies not configured | IP spoofing | Trusts all proxy headers by default |
| JWT secret hardcoded | JWT forgery | `jwtSecret = []byte("secret")` |
| JWT signature algorithm not verified | alg=none bypass | `t.Method` not checked |
| BindJSON binds full struct | Mass Assignment | Struct contains IsAdmin field |
| gin.Default() error exposure | Information disclosure | `err.Error()` returned to client |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `db.Raw("..." + var)` | SQL | GORM raw concatenation |
| `db.Where("..." + var)` | SQL | Where string concatenation |
| `db.Order(userInput)` | SQL blind injection | ORDER BY injection |
| `exec.Command("sh", "-c", var)` | Command injection | Shell execution |
| `c.File("/uploads/" + var)` | Path traversal | Path concatenation |
| `template.HTML(userInput)` | XSS | Unescaped |
| `http.Get(userURL)` | SSRF | URL controllable |
| `c.BindJSON(&fullStruct)` | Mass Assignment | Binds sensitive fields |

## Grep Search Patterns

```
# SQL injection
\.Raw\s*\(.*\+|\.Where\s*\(.*\+|\.Order\s*\(.*c\.(Query|Param)

# Command injection
exec\.Command

# Path traversal
c\.File\s*\(|filepath\.Join.*c\.(Query|Param)

# JWT
jwt.*secret|Secret.*\[\]byte

# CORS
cors\.Default|AllowOrigins.*\*

# Binding
c\.Bind|c\.ShouldBind

# SSRF
http\.Get\s*\(.*c\.(Query|Param)
```

## Audit Checklist

- [ ] GORM Raw/Where/Order string concatenation
- [ ] exec.Command command injection
- [ ] File operation path traversal
- [ ] SSRF (http.Get with user URL)
- [ ] JWT key strength and algorithm verification
- [ ] IDOR (resource ownership not validated)
- [ ] CORS configuration
- [ ] SetTrustedProxies proxy configuration
- [ ] BindJSON binds DTO instead of full struct
- [ ] Error handling does not leak internal information
- [ ] gosec static analysis
