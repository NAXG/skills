# Express Security Cheat Sheet

> Version scope: Express 4.x/5.x, Node.js | Load condition: package.json contains express

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Not using helmet | Missing security headers | No `helmet()` middleware |
| CORS default wide open | Cross-origin attack | `cors()` with no arguments / `origin: '*'` |
| CORS reflects Origin | Credential theft | `callback(null, origin)` + credentials |
| Weak session secret | Session forgery | `secret: 'keyboard cat'` |
| Cookie secure=false | Cookie hijacking | Session cookie transmitted over HTTP |
| Incorrect middleware order | Security bypass | Routes placed before security middleware |
| Error stack leakage | Information disclosure | `err.stack` returned to client |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `exec(cmd)` / `spawn("sh","-c",cmd)` | Command injection | shell=true |
| `User.findOne({...req.body})` | NoSQL injection | `{$gt:""}` bypass |
| `_.merge(obj, req.body)` | Prototype pollution | `__proto__` injection |
| `Object.assign(obj, req.body)` | Prototype pollution | Same as above |
| `res.sendFile(path+input)` | Path traversal | path.basename not used |
| `<%- var %>` (EJS) | XSS | Unescaped output |
| `{{{var}}}` (Handlebars) | XSS | Triple braces unescaped |
| `!{var}` (Pug) | XSS | Unescaped output |
| `eval()` / `Function()` | Code injection | User input execution |

## Grep Search Patterns

```
# Command injection
exec\s*\(|spawn\s*\(|child_process

# NoSQL injection
findOne\s*\(|find\s*\(|updateOne\s*\(

# Prototype pollution
\.merge\s*\(|Object\.assign\s*\(|__proto__

# XSS
<%-|{{{

# Path traversal
sendFile\s*\(|res\.download\s*\(

# CORS
cors\s*\(\s*\)|origin:\s*['"]?\*|callback\s*\(null,\s*origin\)

# Session
secret:\s*['"][^'"]{1,20}['"]
```

## Audit Checklist

- [ ] Whether helmet middleware is enabled
- [ ] CORS origin configuration (avoid * or reflection)
- [ ] exec/spawn command injection
- [ ] MongoDB query input type validation (NoSQL injection)
- [ ] _.merge / Object.assign (prototype pollution)
- [ ] Template engine unescaped markers (<%-, {{{, !{)
- [ ] sendFile/download path traversal
- [ ] Session secret strength and cookie security configuration
- [ ] Whether error handling leaks stack traces
- [ ] npm audit dependency vulnerabilities
