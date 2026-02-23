# Go Security Audit

> Go security audit module | See references/agent-contract.md for methodology
> Applicable to: Go, Gin, Echo, Fiber, net/http, fasthttp

---

## Sources (User Input Points)

| Framework | API |
|-----------|-----|
| net/http | `r.URL.Query().Get()`, `r.FormValue()`, `r.Header.Get()`, `r.Cookie()` |
| Gin | `c.Query()`, `c.PostForm()`, `c.Param()`, `c.GetHeader()` |
| Echo | `c.QueryParam()`, `c.FormValue()`, `c.Param()` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Gosec | Dangerous Functions |
|-----------|--------------|-----|-------|---------------------|
| SQL Execution | SQL Injection | 89 | G201/G202 | `db.Query(fmt.Sprintf(...))` |
| Command Execution | Command Injection | 78 | G204 | `exec.Command("sh", "-c", cmd)` |
| File Operations | Path Traversal | 22 | G304/G305 | `os.Open(userPath)`, `zip.OpenReader` |
| HTTP Requests | SSRF | 918 | G107 | `http.Get(userURL)` |
| Templates | XSS/SSTI | 79 | G203 | `template.HTML()`, `text/template` |

---

## Go Specific Dangerous Patterns

### text/template vs html/template
```go
import "text/template"   // no auto HTML escaping, XSS risk
import "html/template"   // auto-escaping, but the following are still dangerous:
template.HTML(userInput)  // explicitly marked as safe, bypasses escaping
template.JS(userInput)
template.CSS(userInput)
```

### filepath.Join Does Not Prevent Path Traversal
```go
filepath.Join("/uploads", "../../etc/passwd")  // = "/etc/passwd"
// must validate that the final path is within the target directory
```

### Goroutine Concurrency Safety (Merged from go_security.md)
```go
// Dangerous: concurrent read/write to map (DATA RACE)
var cache = make(map[string]string)
// Go map is not thread-safe, concurrent read/write will panic

// Dangerous: unbuffered channel causing goroutine leak
ch := make(chan int)
go func() { ch <- result }()  // blocks forever if no receiver
```

### strconv.Atoi Integer Overflow
```go
size, _ := strconv.Atoi(input)
smallSize := int16(size)  // 65536 → 0, overflow!
```

### pprof Exposure
```go
import _ "net/http/pprof"  // automatically exposes /debug/pprof
```

---

## Grep Search Patterns

```regex
# Command execution (G204)
exec\.Command|exec\.CommandContext|syscall\.Exec

# SQL injection (G201/G202)
fmt\.Sprintf.*(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)
db\.(Query|Exec|Raw)\s*\([^)]*\+
NamedQuery\s*\([^)]*\+

# Template injection (G203)
template\.New.*Parse\(|text/template
template\.(HTML|JS|CSS)\s*\(

# SSRF (G107)
http\.(Get|Post|Do|NewRequest)\s*\(
net\.(Dial|DialTimeout|DialTCP)\s*\(

# Path traversal (G304/G305)
filepath\.Join|os\.(Open|Create|ReadFile)|ioutil\.ReadFile
zip\.OpenReader|archive/(zip|tar)

# Integer overflow (G109)
strconv\.Atoi.*int(8|16|32)

# Weak random (G404)
"math/rand"|rand\.(Int|Intn|Seed)

# Hardcoded credentials (G101)
(password|passwd|secret|token|apikey|api_key)\s*[:=]\s*["'][^"']+["']

# pprof exposure (G108)
net/http/pprof|/debug/pprof

# Insecure SSH (G106)
InsecureIgnoreHostKey

# unsafe usage (G103)
unsafe\.Pointer|uintptr\(unsafe

# Decompression bomb (G110)
gzip\.NewReader|zlib\.NewReader|flate\.NewReader

# Insecure TLS (G402)
InsecureSkipVerify|MinVersion.*tls\.VersionTLS1[01]

# CORS
AllowOrigins|AllowAllOrigins|AllowCredentials|AllowOriginFunc

# JWT
jwt\.Parse|jwt\.ParseWithClaims|jwtKey|signingKey

# Concurrency safety
make\(chan|go func\(
sync\.Mutex|sync\.RWMutex|sync\.Map

# Log injection
log\.Printf.*%s|fmt\.Printf.*%s
```

---

## Gosec Rules Quick Reference

| Category | Rule | Description |
|----------|------|-------------|
| Credentials | G101 | Hardcoded credentials |
| Binding | G102 | Binding to 0.0.0.0 |
| unsafe | G103 | Usage of unsafe package |
| Errors | G104 | Unchecked error return values |
| SSH | G106 | InsecureIgnoreHostKey |
| SSRF | G107 | Tainted URL input |
| pprof | G108 | Automatic pprof exposure |
| Overflow | G109 | Atoi to smaller type conversion |
| Decompression | G110 | Decompression bomb |
| SQL | G201/G202 | SQL concatenation |
| XSS | G203 | Unescaped template |
| Command | G204 | Command execution |
| Path | G304/G305 | Path traversal / Zip Slip |
| Crypto | G401-G404 | Weak crypto / weak random |

---

## Audit Checklist

### Command Execution
- [ ] `exec.Command` / `exec.CommandContext`
- [ ] Check for `"sh", "-c"` pattern calls

### SQL Injection
- [ ] `fmt.Sprintf` + SQL keywords
- [ ] `db.Query/Exec/Raw` + string concatenation
- [ ] GORM `db.Raw()` / Sqlx `NamedQuery`

### Template Injection
- [ ] Distinguish between `text/template` and `html/template`
- [ ] Search for `template.HTML/JS/CSS`
- [ ] Search for `template.Parse(user input)`

### SSRF
- [ ] `http.Get/Post/Do/NewRequest` + user URL
- [ ] `net.Dial` + user address
- [ ] Redirect handling (CheckRedirect)

### File Operations
- [ ] `filepath.Join` + user input → validate final path
- [ ] zip/tar extraction (Zip Slip)
- [ ] Decompression size limits (`io.LimitReader`)

### Concurrency Safety
- [ ] Shared map without lock protection
- [ ] Goroutine leaks (unbuffered channels)
- [ ] Error handling (G104)

### Authorization Focus
- [ ] Route group middleware configuration (Gin `Use()` / Echo `Use()`)
- [ ] DELETE/PUT handler resource ownership validation
- [ ] JWT key strength and algorithm verification

### Configuration Security
- [ ] CORS configuration (`AllowOrigins: ["*"]` + Credentials)
- [ ] pprof endpoint exposure
- [ ] Hardcoded passwords/keys
- [ ] TLS configuration (InsecureSkipVerify)
