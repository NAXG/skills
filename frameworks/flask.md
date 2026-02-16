# Flask Security Cheat Sheet

> Version scope: Flask 2.x/3.x, Werkzeug | Load condition: flask import or app.run detected

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| debug=True in production | RCE (Werkzeug debugger PIN computable) | `app.run(debug=True)` |
| SECRET_KEY hardcoded/weak | Session forgery/CSRF bypass | `secret_key = 'super_secret'` |
| SECRET_KEY = os.urandom(16) | Sessions invalidated on restart | Different key generated each time |
| PickleSerializer session | RCE (combined with SECRET_KEY leakage) | `SESSION_SERIALIZER = PickleSerializer` |
| No CSRFProtect | CSRF | Not using Flask-WTF |
| CORS wide open | Cross-origin attack | `CORS(app)` with no arguments |
| SESSION_COOKIE_SECURE=False | Cookie hijacking | Transmitted over HTTP |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `render_template_string(f"...{var}")` | SSTI (Critical) | User input enters template |
| `render_template(user_input)` | SSTI | User controls template name |
| `Markup(f"...{var}")` | XSS | Bypasses escaping |
| `|safe` template filter | XSS | Bypasses escaping |
| `return f'<h1>{var}</h1>'` | XSS | Directly returns HTML |
| `db.engine.execute(f"...{var}")` | SQL | String concatenation |
| `text(f"...{var}")` | SQL | SQLAlchemy text concatenation |
| `os.system(f"...{var}")` | Command injection | Shell execution |
| `subprocess.run(cmd, shell=True)` | Command injection | shell=True |
| `send_file(f"/uploads/{var}")` | Path traversal | secure_filename not used |
| `requests.get(user_url)` | SSRF | URL not validated |
| `redirect(request.args['next'])` | Open redirect | Target not validated |

## Grep Search Patterns

```
# SSTI (highest priority)
render_template_string|Template\s*\(

# Debug mode
debug\s*=\s*True|FLASK_DEBUG

# SECRET_KEY
secret_key\s*=|SECRET_KEY\s*=

# XSS
Markup\s*\(|\|safe|return.*f['"'].*<

# SQL injection
execute\s*\(.*f['"']|execute\s*\(.*\+
text\s*\(.*f['"']|text\s*\(.*\+

# Command injection
os\.system|subprocess\.|popen

# File operations
send_file|send_from_directory|open\s*\(

# Session
SESSION_SERIALIZER|PickleSerializer|pickle
```

## Audit Checklist

- [ ] DEBUG mode disabled in production
- [ ] SECRET_KEY not hardcoded or weak
- [ ] render_template_string usage (SSTI)
- [ ] SQL queries parameterized
- [ ] Command execution functions (os.system/subprocess)
- [ ] File operation path traversal (send_file)
- [ ] SSRF (requests.get with user URL)
- [ ] CSRF protection (Flask-WTF CSRFProtect)
- [ ] Session configuration (secure/httponly/samesite)
- [ ] CORS configuration
- [ ] Pickle session serialization
