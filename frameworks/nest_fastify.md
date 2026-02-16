# NestJS / Fastify Security Cheat Sheet

> Version scope: NestJS 9+, Fastify 4+ | Load condition: @nestjs/core or fastify detected

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| @Public() bypasses global Guard | Authentication bypass | Sensitive endpoint annotated with @Public |
| Incorrect Guard order | Authorization bypass | RolesGuard placed before JwtAuthGuard |
| WebSocket Gateway without Guard | Unauthenticated WS | `@WebSocketGateway` without `@UseGuards` |
| ValidationPipe not globally enabled | Input not validated | main.ts missing useGlobalPipes |
| ValidationPipe without whitelist | Mass Assignment | Extra fields not filtered |
| enableCors() with no arguments | CORS wide open | Default allows all origins |
| JWT secret hardcoded/weak | JWT forgery | `secret: 'secret'` |
| JWT without expiresIn | Token never expires | sign() without expiration config |
| trustProxy: true | IP spoofing | Fastify trusts all proxies |
| Fastify multipart without limits | DoS | No file size limit |
| Entity returned directly | Sensitive field leakage | Returns entity containing password |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `.query(\`...${var}\`)` | SQL | TypeORM raw concatenation |
| `.find(req.body)` | NoSQL injection | MongoDB `{$gt:""}` |
| `FileInterceptor('file')` without fileFilter | Arbitrary upload | No type restriction |
| `join(path, file.originalname)` | Path traversal | Filename not sanitized |
| `error.stack` returned to client | Information disclosure | InternalServerErrorException |

## Grep Search Patterns

```
# Guard bypass
@Public|@WebSocketGateway(?!.*@UseGuards)

# Missing validation
ValidationPipe\s*\(\s*\)|@Body\s*\(\s*\)

# SQL/NoSQL injection
\.query\s*\(.*\$\{|\.find\s*\(.*params|\.findOne\s*\(.*body

# CORS
enableCors\s*\(\s*\)|origin:\s*true

# File upload
FileInterceptor(?!.*fileFilter)

# JWT
secret:\s*['"][^'"]{1,20}['"]|JwtModule\.register(?!Async)

# Sensitive leakage
throw.*error\.(message|stack)

# Fastify
trustProxy:\s*true|register\(multipart(?!.*limits)
```

## Audit Checklist

- [ ] Global Guard configuration and @Public() usage
- [ ] Guard execution order (authenticate before authorize)
- [ ] WebSocket Gateway authentication
- [ ] Global ValidationPipe with whitelist/forbidNonWhitelisted
- [ ] DTO decorator completeness (class-validator)
- [ ] TypeORM/MongoDB query injection
- [ ] CORS origin configuration
- [ ] JWT key strength, algorithm, expiration time
- [ ] File upload type/size limits
- [ ] Entity serialization excludes sensitive fields (@Exclude)
- [ ] Fastify trustProxy / multipart limits
- [ ] Error handling does not leak stack traces
