# Rust Security Audit

> Rust security audit module | See references/agent-contract.md for methodology
> Applicable to: Actix-web, Axum, Rocket, Tonic (gRPC), Tauri

---

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| unsafe Code | Memory Safety | 787 | `unsafe {}`, `unsafe fn`, `unsafe impl` |
| Command Execution | Command Injection | 78 | `Command::new`, `std::process` |
| SQL Execution | SQL Injection | 89 | `query` + `format!` |
| File Operations | Path Traversal | 22 | `fs::read`, `File::open` |
| FFI | Memory Safety | 787 | `extern "C"`, `libc::` |
| Deserialization | Logic Vulnerabilities | 502 | `serde_json::from_str` (custom Deserialize) |

---

## Rust Specific Dangerous Patterns

### unsafe Code Blocks
```rust
unsafe {
    // bypasses all Rust safety guarantees
    // raw pointer dereference, FFI calls, mutable static variables
    let ptr = 0x12345 as *const i32;
    println!("{}", *ptr);  // undefined behavior
}
```

### FFI Boundaries (All FFI Calls Are unsafe)
```rust
extern "C" {
    fn external_func(buf: *mut u8, len: usize);  // C functions are not protected by Rust memory safety
}
```

### Tauri Desktop Application Specifics
```rust
// Dangerous: frontend can invoke backend commands
#[tauri::command]
fn read_file(path: String) -> String {  // path not validated
    std::fs::read_to_string(path).unwrap()
}

// Dangerous: allowlist too permissive
// tauri.conf.json: "allowlist": { "all": true }
```

### format! Macro SQL Injection
```rust
// Dangerous
let query = format!("SELECT * FROM users WHERE name = '{}'", name);
sqlx::query(&query).fetch_all(&pool).await?;

// Safe
sqlx::query("SELECT * FROM users WHERE name = $1")
    .bind(&name)
    .fetch_all(&pool).await?;
```

---

## Grep Search Patterns

```regex
# unsafe
unsafe\s*\{|unsafe\s+fn|unsafe\s+impl

# Raw pointers
\*const\s|\*mut\s
\.as_ptr\(|\.as_mut_ptr\(|from_raw_parts

# FFI
extern\s*"C"|#\[no_mangle\]|libc::

# Command execution
Command::new|std::process::Command
\.arg\(|\.args\(|\.output\(|\.spawn\(

# SQL injection
format!\s*\(".*SELECT|format!\s*\(".*INSERT|format!\s*\(".*UPDATE
query\s*\(&format!|query_as\s*\(&format!

# File operations
fs::(read|write|remove|create_dir)|File::(open|create)
std::path::Path

# Deserialization
serde_json::from_(str|value|reader|slice)
serde_yaml::from_|bincode::deserialize
serde::Deserialize

# Cryptography
rand::thread_rng|OsRng|rand::Rng
ring::|openssl::|rustls::

# Web frameworks
actix_web::|axum::|rocket::|warp::
HttpRequest|HttpResponse|Json<

# Tauri
tauri::command|tauri\.conf\.json
allowlist|invoke_handler
window\.__TAURI__|ipc

# Error handling
\.unwrap\(\)|\.expect\(|panic!

# Unsafe trait implementations
unsafe\s+impl\s+(Send|Sync)

# Memory operations
std::mem::(transmute|forget|uninitialized)
ManuallyDrop|MaybeUninit

# Hardcoded credentials
(password|secret|token|api_key)\s*[:=]\s*"[^"]*"

# CORS
cors|CorsLayer|AllowOrigin
```

---

## Dangerous Crates Quick Reference

| Crate | Risk | Notes |
|-------|------|-------|
| `libc` | Memory safety | C bindings, all calls require unsafe |
| `nix` | System call safety | Low-level system operations |
| `rusqlite` | SQL injection | `execute` + `format!` |
| `sqlx` | SQL injection | `query` + `format!` |
| `hyper` | HTTP handling | Low-level, beware of request smuggling |

---

## Audit Checklist

### unsafe Code
- [ ] Audit all `unsafe` blocks
- [ ] Raw pointer operation validation
- [ ] `unsafe impl Send/Sync` correctness

### FFI
- [ ] `extern "C"` boundary parameter validation
- [ ] C library memory management (who is responsible for freeing)
- [ ] `#[no_mangle]` exported function safety

### Command Execution
- [ ] `Command::new` with controllable parameters
- [ ] Shell invocation (`sh -c`)

### SQL Injection
- [ ] `format!` + SQL queries
- [ ] Using parameterized queries (`$1`, `?`)

### File Operations
- [ ] Path concatenation + user input
- [ ] Path traversal validation

### Tauri Focus
- [ ] `tauri::command` parameter validation
- [ ] `allowlist` minimal privilege configuration
- [ ] IPC message validation

### Memory Safety
- [ ] `mem::transmute` type casting
- [ ] `mem::forget` resource leaks
- [ ] `MaybeUninit` initialization validation

### Error Handling
- [ ] `.unwrap()` / `panic!` in production code
- [ ] Sensitive information leakage (error messages)
