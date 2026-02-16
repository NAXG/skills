# Rust Web Security Cheat Sheet

> Version scope: Actix-web 4.x, Axum 0.7+, Rocket 0.5+ | Load condition: Cargo.toml contains actix-web/axum/rocket

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Cors::permissive() | CORS wide open | Actix allows all |
| allow_any_origin + supports_credentials | Credential theft | Dangerous combination |
| validate_exp = false | JWT never expires | jsonwebtoken configuration |
| Json\<serde_json::Value\> | Missing validation | Generic type without schema |
| unwrap()/expect() in handler | DoS/panic | Request triggers panic |
| unsafe block | Memory safety violation | Breaks Rust safety guarantees |
| Arc\<Mutex\> TOCTOU | Race condition | Lock released before operation |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `sqlx::query(&format!("SELECT...{}", var))` | SQL | format! concatenation |
| `diesel::sql_query(format!(...))` | SQL | Same as above |
| `Statement::from_string(format!(...))` | SQL | sea-orm concatenation |
| `NamedFile::open(format!("./uploads/{}", var))` | Path traversal | Path concatenation |
| `tokio::fs::read(format!(...))` | Path traversal | Same as above |
| `reqwest::get(&user_url)` | SSRF | URL controllable |
| `unsafe { ... }` | Memory safety | Requires manual review |
| `std::mem::transmute` | Memory safety | Type conversion |
| `from_raw_parts` | Memory safety | Pointer operations |

## Grep Search Patterns

```
# SQL injection
format!\s*\(.*SELECT|format!\s*\(.*INSERT|format!\s*\(.*UPDATE|format!\s*\(.*DELETE
sql_query\s*\(format!|query\s*\(&format!|query_as.*&format!

# Path traversal
NamedFile::open\s*\(format!|tokio::fs::read.*format!|std::fs::read.*format!

# SSRF
reqwest::(get|Client).*params|hyper::Uri.*parse.*input

# Unsafe
unsafe\s*\{|transmute|from_raw_parts

# Race conditions
\.lock\(\).*drop|\.read\(\).*\.write\(\)

# JWT
validate_exp.*false|from_secret.*b"[^"]{1,16}"

# CORS
Cors::permissive|allow_any_origin

# Input validation
Json<serde_json::Value>|Json<Value>

# DoS
\.unwrap\(\)|\.expect\(
```

## Audit Checklist

- [ ] cargo audit dependency vulnerabilities
- [ ] format! with SQL keywords (SQL injection)
- [ ] NamedFile::open / tokio::fs::read path concatenation
- [ ] reqwest/hyper user-controlled URL (SSRF)
- [ ] All unsafe blocks manually reviewed
- [ ] Arc\<Mutex\>/RwLock race conditions
- [ ] jsonwebtoken configuration (algorithm/expiration/key)
- [ ] Cors::permissive / allow_any_origin
- [ ] Json\<Value\> untyped input
- [ ] unwrap()/expect() in request handlers (DoS)
- [ ] .env / dotenv hardcoded keys
