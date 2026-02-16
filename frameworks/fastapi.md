# FastAPI Security Cheat Sheet

> Version scope: FastAPI 0.100+, Starlette, SQLAlchemy | Load condition: fastapi import detected

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Endpoint without Depends(auth) | Missing authentication | Route without auth dependency |
| Parameter type is dict | Validation bypass | `def f(data: dict)` without schema |
| No response_model | Sensitive field leakage | Returns ORM object containing password_hash |
| CORSMiddleware allow_origins=["*"] | Cross-origin attack | CORS wide open |
| BackgroundTasks with user input | RCE | `add_task(os.system, cmd)` |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `db.execute(f"...{var}")` | SQL | SQLAlchemy concatenation |
| `text(f"...{var}")` | SQL | SQLAlchemy text concatenation |
| `BackgroundTasks.add_task(os.system, var)` | Command injection | Background task |
| `open(f"/uploads/{file.filename}")` | Path traversal | Filename not sanitized |
| `def f(data: dict)` | Validation bypass | No Pydantic schema |

## Grep Search Patterns

```
# Routes
@(app|router)\.(get|post|put|delete|patch)\s*\(

# Pydantic bypass
def\s+\w+\([^)]*:\s*dict[^)]*\)

# Background tasks
BackgroundTasks\.add_task

# SQL injection
db\.execute\s*\(f['"']|text\s*\(f['"']

# File upload
UploadFile.*file\.filename
```

## Audit Checklist

- [ ] All endpoints have appropriate auth Depends
- [ ] Pydantic schema used (not dict)
- [ ] response_model excludes sensitive fields
- [ ] SQLAlchemy raw SQL / text() concatenation
- [ ] BackgroundTasks parameter source
- [ ] File upload path and type validation
- [ ] CORSMiddleware configuration
- [ ] IDOR (path parameters without ownership validation)
