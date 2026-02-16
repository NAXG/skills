# API Security Audit Module

> Loaded when the project has REST / GraphQL / gRPC APIs

## REST API Checklist

### Authentication & Authorization
- [ ] Are all endpoints protected by authentication (whitelisted exceptions must be documented)
- [ ] Is the token transmission method secure (Header vs Query Parameter)
- [ ] Do API Keys have scope/permission restrictions
- [ ] Is the OAuth2 implementation complete (PKCE, state parameter, redirect_uri validation)

### Input Validation
- [ ] Request body size limits
- [ ] Content-Type validation
- [ ] Parameter type validation (do numeric parameters accept strings)
- [ ] Array/nested object depth limits (DoS prevention)
- [ ] Do PUT/PATCH have field whitelists (mass assignment prevention)

### Output Security
- [ ] Does the response leak internal information (stack traces, database table names, internal IPs)
- [ ] Can pagination parameters be abused (page_size=999999)
- [ ] Sensitive field filtering (password hashes, internal IDs, etc.)
- [ ] Do different error codes leak information (404 vs 403 revealing resource existence)

### Rate Limiting
- [ ] Do critical endpoints (login, registration, password reset) have rate limiting
- [ ] Is rate limiting based on IP + user (preventing distributed bypass)

## GraphQL Checklist

- [ ] Query depth limiting (preventing recursive query DoS)
- [ ] Query complexity limiting
- [ ] Batch query limiting (batching attack)
- [ ] Is introspection disabled in production
- [ ] Field-level permission control
- [ ] Permission propagation in relational queries

## CORS Configuration

- [ ] `Access-Control-Allow-Origin: *` + `Credentials: true` is a dangerous combination
- [ ] Is the Origin whitelist strictly validated (cannot use regex substring matching)

## Grep Search Patterns

```
Grep: @RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping
Grep: app\.(get|post|put|delete|patch)\(
Grep: rate.limit|throttle|RateLimit
Grep: page_size|pageSize|limit|offset
Grep: X-RateLimit|Retry-After
Grep: depthLimit|queryComplexity|maxDepth
Grep: introspection|__schema|__type
Grep: type Query|type Mutation|type Subscription
Grep: Access-Control-Allow-Origin|CORS|cors
```

## Cross-References

- Related domain modules: domains/authentication.md (API authentication), domains/authorization.md (API permissions)
