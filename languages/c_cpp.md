# C/C++ Security Audit

> C/C++ security audit module | See references/agent-contract.md for methodology
> Applicable to: C, C++, embedded systems, systems programming

---

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Buffer Overflow | Stack/Heap Overflow | 120/122 | `strcpy`, `sprintf`, `gets`, `strcat`, `scanf` |
| Format String | Information Leak/Write | 134 | `printf(user_input)`, `syslog(user_input)` |
| Integer Overflow | Buffer Issues | 190/191 | `malloc(size + 1)` when size=SIZE_MAX |
| Command Execution | Command Injection | 78 | `system`, `popen`, `exec*` |
| Use After Free | UAF | 416 | `free(ptr); ptr->field` |
| Double Free | Heap Corruption | 415 | `free(ptr); free(ptr)` |
| Race Condition | TOCTOU | 362 | `access()` + `open()` |
| Memory Leak | DoS | 401 | `malloc` without `free` |

---

## C/C++ Specific Dangerous Patterns

### Dangerous Functions → Safe Alternatives

| Dangerous | Safe Alternative | Notes |
|-----------|-----------------|-------|
| `strcpy` | `strncpy` / `strlcpy` | Length-limited |
| `sprintf` | `snprintf` | Buffer size limited |
| `gets` | `fgets` | Removed in C11 |
| `strcat` | `strncat` / `strlcat` | Length-limited |
| `scanf` | `fgets` + `sscanf` | Input length limited |
| `malloc(n*m)` | `calloc(n, m)` | Automatic overflow detection |

### Off-by-one Errors
```c
char buf[10];
for (int i = 0; i <= 10; i++)  // should be < 10
    buf[i] = data[i];
```

### TOCTOU (Time-of-Check-Time-of-Use)
```c
if (access(filename, R_OK) == 0) {  // check
    fd = open(filename, O_RDONLY);    // use (symlink may have been replaced)
}
```

### Uninitialized Variables
```c
int *ptr;         // uninitialized
if (condition)
    ptr = malloc(size);
*ptr = value;     // ptr is uninitialized when condition is false
```

---

## Grep Search Patterns

```regex
# Buffer overflow
strcpy\s*\(|strcat\s*\(|sprintf\s*\(|gets\s*\(
scanf\s*\(|vsprintf\s*\(|sscanf\s*\(
memcpy\s*\(|memmove\s*\(|bcopy\s*\(

# Format string
printf\s*\([^"]*\)|fprintf\s*\([^,]*,[^"]*\)
syslog\s*\([^,]*,[^"]*\)|snprintf\s*\([^,]*,[^,]*,[^"]*\)

# Integer overflow
malloc\s*\(.*\+|alloca\s*\(
size_t.*\*|unsigned.*\+

# Command execution
system\s*\(|popen\s*\(|execl\s*\(|execv\s*\(|execvp\s*\(

# Use after free / double free
free\s*\(|delete\s+|delete\[\]

# Race condition
access\s*\(.*open\s*\(|stat\s*\(.*open\s*\(

# Insecure random
rand\s*\(|srand\s*\(

# Sensitive information
password|secret|key|token|credential

# Insecure memory operations
alloca\s*\(|VLA.*\[.*\]
realloc\s*\(

# C++ specific
const_cast|reinterpret_cast
static_cast.*void\s*\*
\.c_str\s*\(
```

---

## Secure Compilation Options Check

| Option | Compiler Flag | Description |
|--------|--------------|-------------|
| Stack Canary | `-fstack-protector-all` | Stack overflow detection |
| ASLR | `-fPIE -pie` | Address Space Layout Randomization |
| NX | `-z noexecstack` | Non-executable stack |
| RELRO | `-z relro -z now` | GOT write protection |
| Fortify | `-D_FORTIFY_SOURCE=2` | Enhanced buffer function checks |
| CFI | `-fsanitize=cfi` | Control Flow Integrity |
| SafeStack | `-fsanitize=safe-stack` | Stack isolation |

Detection: `checksec --file=binary` or `readelf -l binary | grep STACK`

---

## Audit Checklist

### Buffer Safety
- [ ] Usage of `strcpy`/`sprintf`/`gets`/`strcat`/`scanf`
- [ ] `memcpy`/`memmove` length parameter validation
- [ ] Stack buffer + external input length
- [ ] Off-by-one loop boundaries

### Integer Safety
- [ ] `malloc(size + N)` overflow
- [ ] Integer truncation (int → short)
- [ ] Signed/unsigned comparison

### Memory Safety
- [ ] Pointer set to NULL after `free`
- [ ] `realloc` failure handling
- [ ] Uninitialized variable usage
- [ ] `alloca` / VLA stack overflow

### Format String
- [ ] `printf(user_input)` (should use `printf("%s", input)`)
- [ ] `syslog` format string

### Race Conditions
- [ ] `access()` + `open()` (TOCTOU)
- [ ] Temporary file creation (`mktemp` → `mkstemp`)

### Compilation Security
- [ ] Stack Canary / ASLR / NX / RELRO enabled
- [ ] Compiled with `-D_FORTIFY_SOURCE=2`
