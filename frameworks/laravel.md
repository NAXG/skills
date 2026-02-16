# Laravel Security Cheat Sheet

> Version scope: Laravel 8.x-11.x | Load condition: artisan or composer.json contains laravel

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| APP_DEBUG=true in production | Information disclosure/stack traces/config | `APP_DEBUG=true` in `.env` |
| APP_KEY leakage | Deserialization RCE | .env leaked or exposed via debug page |
| .env not in .gitignore | Credential leakage | `/.env` accessible via HTTP |
| CSRF $except too broad | CSRF | `$except = ['*']` |
| Mass Assignment without $fillable | Privilege escalation/data tampering | `::create($request->all())` |
| {!! $var !!} output | XSS | Blade unescaped |
| dd()/dump() not cleaned up | Information disclosure | Debug output in production |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `User::create($request->all())` | Mass Assignment | Fields not restricted |
| `->fill($request->input())` | Mass Assignment | Same as above |
| `DB::select("..." . $var)` | SQL | Raw concatenation |
| `whereRaw("..." . $var)` | SQL | Raw method concatenation |
| `orderByRaw($request->input())` | SQL | Sort injection |
| `unserialize($input)` | Deserialization RCE | POP chain |
| `{!! $userInput !!}` | XSS | Blade unescaped |
| `Blade::render($userTemplate)` | SSTI (Critical) | User controls template |
| `Storage::get($request->input())` | Path traversal | File path controllable |
| `include($request->input())` | File inclusion (Critical) | LFI/RFI |
| `Http::get($request->input())` | SSRF | URL controllable |
| `exec($var)` / `shell_exec($var)` | Command injection | Shell execution |
| `redirect($request->input())` | Open redirect | Target not validated |
| `simplexml_load_string($input)` | XXE | External entities |

## Grep Search Patterns

```
# Mass Assignment
::create\s*\(\s*\$request->all|->fill\s*\(\s*\$request|->update\s*\(\s*\$request->all

# SQL injection
DB::(select|statement|raw|delete|update|insert)\s*\(.*\$|whereRaw.*\$|orderByRaw.*\$
havingRaw|groupByRaw

# Deserialization
unserialize\s*\(|APP_KEY\s*=

# SSTI/XSS
\{\!\!.*\$|@php.*\$request|Blade::render.*\$

# Path traversal/file inclusion
Storage::(get|put|delete).*\$request|include.*\$request|require.*\$request

# SSRF
Http::(get|post).*\$request|file_get_contents.*\$request

# Command injection
exec\s*\(.*\$|shell_exec|system\s*\(|passthru

# CSRF
VerifyCsrfToken.*\$except

# Sensitive information
APP_DEBUG=true|dd\(|dump\(|var_dump\(

# Open redirect
redirect\s*\(\s*\$request

# XXE
simplexml_load_(string|file)|DOMDocument.*loadXML
```

## Audit Checklist

- [ ] .env in .gitignore and not accessible via HTTP
- [ ] APP_DEBUG production configuration
- [ ] Model $fillable/$guarded defined
- [ ] create/fill/update using $request->all()
- [ ] whereRaw/orderByRaw SQL injection
- [ ] unserialize and APP_KEY leakage
- [ ] {!! !!} Blade unescaped output
- [ ] File operation path concatenation
- [ ] Http::get / file_get_contents SSRF
- [ ] exec/shell_exec command injection
- [ ] VerifyCsrfToken $except scope
- [ ] redirect open redirect
- [ ] Login/registration endpoint rate limiting
