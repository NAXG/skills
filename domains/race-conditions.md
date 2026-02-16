# Race Condition Security Audit Module

> Loaded when the project has concurrent operation scenarios (multi-threaded/async/distributed)

## TOCTOU (Time-of-Check to Time-of-Use)

- [ ] Are check + operation within the same transaction/lock
- [ ] File system: `access()` followed by `open()` (file may be replaced/symlink attack in between)
- [ ] Database: SELECT then UPDATE (without `SELECT FOR UPDATE`)
- [ ] Balance/inventory check then deduction (may be consumed by another request in between)

## Concurrent Data Structure Safety

- [ ] Non-thread-safe collections used in multi-threaded context: Java `HashMap`/`ArrayList`/`SimpleDateFormat`, Go `map` concurrent read/write
- [ ] Global variables/singletons accessed concurrently without synchronization
- [ ] Concurrent read/write to cache

### Language-Specific Pitfalls
- **Java**: Concurrent `HashMap` put causes infinite loop (Java 7) or data loss; `SimpleDateFormat` is not thread-safe, use `DateTimeFormatter` instead
- **Go**: Concurrent `map` read/write causes panic; use `sync.RWMutex` or `sync.Map`
- **Python**: GIL does not guarantee atomicity of compound operations; `counter += 1` is still read-modify-write

## Distributed Race Conditions

- [ ] Is the distributed lock implementation correct (Redis SETNX + expiration + renewal + fencing token)
- [ ] Lock renewal: lock expires after task timeout, another instance acquires lock causing dual writes
- [ ] Is message queue consumption idempotent (same message may be delivered multiple times)
- [ ] Optimistic lock version check (`@Version` / `WHERE version = ?`)

## Async & File System Race Conditions

- [ ] Is Promise/Future exception handling complete
- [ ] Goroutine leaks (Go: goroutines without exit conditions)
- [ ] Is temporary file creation secure (`mkstemp` vs `tmpnam`)

## Grep Search Patterns

```
Grep: access\(|stat\(|exists\(
Grep: SELECT.*FOR UPDATE|LOCK IN SHARE MODE
Grep: balance|stock
Grep: new HashMap|new ArrayList|SimpleDateFormat
Grep: sync\.Map|sync\.Mutex|sync\.RWMutex
Grep: ConcurrentHashMap|CopyOnWriteArrayList|BlockingQueue
Grep: threading\.Lock|asyncio\.Lock|multiprocessing
Grep: synchronized|ReentrantLock|AtomicInteger|volatile
Grep: SETNX|SET.*NX|redlock|distributed.*lock
Grep: idempotent|dedup
Grep: @Version|version.*=|optimistic.*lock
Grep: @Transactional.*SERIALIZABLE|isolation.*level
Grep: go func|go \w+\(|goroutine
Grep: async\s+def|await\s|Promise\.|CompletableFuture
Grep: mkstemp|tmpnam|tempnam|mktemp(?!p)
Grep: -race|go test.*-race
```

## Cross-References

- Related domain modules: domains/authentication.md (login race conditions/double submit), domains/file-operations.md (TOCTOU file race conditions)
