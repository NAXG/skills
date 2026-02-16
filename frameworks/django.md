# Django Security Cheat Sheet

> Version scope: Django 3.x/4.x/5.x, DRF | Load condition: manage.py or settings.py detected

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| DEBUG=True in production | Information disclosure/stack traces/config | `DEBUG = True` |
| ALLOWED_HOSTS=['*'] | Host header attack | `ALLOWED_HOSTS = ['*']` |
| SECRET_KEY hardcoded/weak | Session forgery | `SECRET_KEY = 'django-insecure-'` |
| CsrfViewMiddleware commented out | CSRF | Missing from middleware list |
| debug_toolbar in production | Information disclosure | `INSTALLED_APPS` contains `debug_toolbar` |
| SESSION_COOKIE_SECURE=False | Cookie hijacking | Session transmitted over HTTP |
| Default admin path | Enumeration/brute force | `path('admin/', admin.site.urls)` |
| ORM filter(**dict) | Lookup injection | Controllable parameter names -> `__contains`, `__regex` |
| Double formatting SSTI | SECRET_KEY leakage | `% name` followed by `.format(user=)` |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `.raw(f"...{var}")` | SQL | String-concatenated raw SQL |
| `.extra(where=[f"..."])` | SQL | where parameter concatenation |
| `RawSQL(f"...")` | SQL | Annotation expression concatenation |
| `cursor.execute("..." % var)` | SQL | Format string concatenation |
| `.filter(**user_dict)` | Lookup injection | Controllable parameter names |
| `mark_safe(user_input)` | XSS | Bypasses auto-escaping |
| `|safe` template filter | XSS | Same as above |
| `{% autoescape off %}` | XSS | Disables auto-escaping |
| `HttpResponse("..." % var)` | XSS | Direct HTML concatenation |
| `render_template_string` equivalent | SSTI | Format string `{user.password}` |
| `redirect(request.GET['next'])` | Open redirect | Target not validated |
| `os.path.join(dir, filename)` | Path traversal | FileResponse filename not sanitized |

## Grep Search Patterns

```
# ORM injection
\.raw\s*\(f['"']|\.raw\s*\([^)]*%\s*str\(
\.extra\s*\([^)]*WHERE\s*=\s*\[|\.extra\s*\([^)]*where\s*=
RawSQL\s*\(f['"']
cursor\.execute\s*\([^)]*['"]\s*%|execute\s*\([^)]*\+
\.filter\s*\(\*\*|\.create\s*\(\*\*

# XSS
mark_safe\s*\(|\|safe\s*}}|autoescape\s+off
HttpResponse\s*\([^)]*%|HttpResponse\s*\(f['"']

# SSTI / format string
['"]\s*%\s*[^'"]*\.format\s*\(

# CSRF
@csrf_exempt|csrf_exempt
CsrfViewMiddleware.*#

# Configuration
DEBUG\s*=\s*True|ALLOWED_HOSTS\s*=\s*\[['"]?\*['"]?\]

# SECRET_KEY
SECRET_KEY\s*=\s*['"][^'"]{0,30}['"]

# File operations
request\.FILES\s*\[|request\.FILES\.get\s*\(
FileResponse\s*\(open\s*\(|open\s*\([^)]*file\.name

# Redirect
redirect\s*\([^)]*request\.|HttpResponseRedirect\s*\([^)]*request\.
```

## Audit Checklist

- [ ] DEBUG / ALLOWED_HOSTS / SECRET_KEY configuration
- [ ] SESSION_COOKIE_SECURE / HTTPONLY / SAMESITE
- [ ] .raw() / .extra() / RawSQL / cursor.execute() SQL concatenation
- [ ] .filter(**dict) controllable parameter names (lookup injection)
- [ ] mark_safe / |safe / autoescape off (XSS)
- [ ] Double formatting (% + .format) leading to SSTI
- [ ] @csrf_exempt decorator usage
- [ ] CSRF_TRUSTED_ORIGINS scope
- [ ] File upload type/size/path validation
- [ ] Whether admin path is default
- [ ] redirect() target from user input
- [ ] debug_toolbar removed in production
