# Koa Security Cheat Sheet

> Version scope: Koa 2.x | Load condition: package.json contains koa

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Incorrect middleware order | Security bypass | Routes placed before helmet/cors/auth |
| Not using koa-helmet | Missing security headers | No helmet middleware |
| CORS origin='*' | Cross-origin attack | `cors({origin: '*'})` |
| CORS reflects Origin | Credential theft | `origin: ctx => ctx.headers.origin` |
| bodyParser default configuration | Prototype pollution | No __proto__ filtering |
| No CSRF middleware | CSRF | Koa has no built-in CSRF |
| Error stack leakage | Information disclosure | `ctx.body = err.stack` |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `Object.assign(obj, ctx.request.body)` | Prototype pollution | `__proto__` injection |
| `_.merge(obj, ctx.request.body)` | Prototype pollution | Same as above |
| `User.findOne(ctx.query)` | NoSQL injection | `{$ne: null}` bypass |
| `exec(\`...${ctx.query.host}\`)` | Command injection | Shell execution |
| `fs.readFile(path.join(dir, ctx.query.file))` | Path traversal | Path not validated |
| `axios.get(ctx.query.url)` | SSRF | URL controllable |
| `jwt.decode(token)` | JWT bypass | Signature not verified (not verify) |
| `ctx.redirect(ctx.query.url)` | Open redirect | Target not validated |

## Grep Search Patterns

```
# Prototype pollution
Object\.assign.*ctx\.request\.body|_\.merge.*ctx\.request\.body

# NoSQL injection
findOne\(ctx\.query\)|find\(ctx\.request\.body\)

# SSRF
axios\.(get|post).*ctx\.query|fetch\(ctx\.query

# Path traversal
fs\.readFile.*ctx\.query|createReadStream.*ctx\.query

# Command injection
exec\(.*ctx\.|spawn\(.*ctx\.

# JWT
jwt\.decode\((?!.*verify)|algorithm.*none

# CORS
cors.*origin:.*\*

# Open redirect
ctx\.redirect\(ctx\.query

# Information disclosure
console\.log.*password|ctx\.body.*process\.env
```

## Audit Checklist

- [ ] Middleware order (security middleware should precede routes)
- [ ] Object.assign/_.merge prototype pollution
- [ ] MongoDB query input type validation
- [ ] File operation path traversal
- [ ] HTTP request SSRF
- [ ] exec/spawn command injection
- [ ] JWT verification logic (verify not decode)
- [ ] CORS configuration
- [ ] CSRF protection (koa-csrf)
- [ ] Error handling does not leak information
- [ ] npm audit dependency vulnerabilities
