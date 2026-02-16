# Python Security Audit

> Python security audit module | See references/agent-contract.md for methodology
> Applicable to: Python 2.x/3.x, Flask, Django, FastAPI, Tornado

---

## Sources (User Input Points)

| Framework | API |
|-----------|-----|
| Flask | `request.args`, `request.form`, `request.json`, `request.files`, `request.headers`, `request.cookies` |
| Django | `request.GET`, `request.POST`, `request.body`, `request.META`, `request.FILES` |
| FastAPI | Function parameters (Query/Path/Body/Header/Cookie) |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Command Execution | Command Injection | 78 | `os.system`, `subprocess` (shell=True), `os.popen` |
| Code Execution | Code Injection | 94 | `eval`, `exec`, `compile`, `__import__` |
| SQL Execution | SQL Injection | 89 | `cursor.execute` (concatenation), `raw()`, `extra()` |
| File Operations | Path Traversal | 22 | `open()`, `send_file`, `os.path.join` |
| Deserialization | RCE | 502 | `pickle.load`, `yaml.load`, `jsonpickle.decode` |
| Template Engine | SSTI | 97 | `render_template_string`, `Template().render` |
| HTTP Requests | SSRF | 918 | `requests.get`, `urllib.urlopen`, `httpx` |

---

## Python Specific Dangerous Patterns

### f-string / format Injection
```python
# 危险: 用户输入作为格式化模板
user_input.format(**locals())  # 可泄露局部变量
f"{user_input}"                # f-string 本身安全，但双重格式化危险

# Django 双重格式化
template = "Hello %s" % user_input  # user_input = "{settings.SECRET_KEY}"
template.format(settings=settings)  # 泄露 SECRET_KEY
```

### yaml.load Must Specify SafeLoader
```python
# 危险
yaml.load(data)                    # 默认 FullLoader，RCE
yaml.load(data, Loader=yaml.Loader)  # FullLoader，RCE

# 安全
yaml.safe_load(data)               # 等价于 SafeLoader
yaml.load(data, Loader=yaml.SafeLoader)
```

### Django filter(**dict) Parameter Name Injection
```python
# 危险: 用户可控字段名
User.objects.filter(**request.GET.dict())
# 攻击: ?password__startswith=a → 逐字符猜测密码
```

### Deserialization (Merged from python_deserialization.md)

| Library | Dangerous Function | Exploitation Difficulty | Notes |
|---------|-------------------|------------------------|-------|
| pickle | `pickle.load/loads/Unpickler` | Very Low | `__reduce__` direct execution |
| PyYAML | `yaml.load` (not SafeLoader) | Very Low | `!!python/object/apply:` |
| jsonpickle | `jsonpickle.decode` | Low | Similar to pickle |
| shelve | `shelve.open` | Low | Uses pickle underneath |
| marshal | `marshal.load` | Medium | Can execute bytecode |
| dill | `dill.load/loads` | Very Low | Extended pickle |

---

## Grep Search Patterns

```regex
# Command execution
os\.system\s*\(|os\.popen\s*\(|subprocess\.(call|run|Popen|check_output)
shell\s*=\s*True|platform\.popen|pty\.spawn

# Code execution
\beval\s*\(|\bexec\s*\(|compile\s*\(|__import__\s*\(
getattr\s*\(.*request|setattr\s*\(.*request

# Deserialization
pickle\.(load|loads|Unpickler)|cPickle\.(load|loads)
yaml\.load\s*\((?!.*SafeLoader)|yaml\.unsafe_load
jsonpickle\.decode|shelve\.open|marshal\.load|dill\.(load|loads)

# SSTI
render_template_string\s*\(|Template\s*\(.*\)\.render
Mako.*Template|tornado.*template.*render

# SQL injection
\.execute\s*\(.*[%f"\+]|\.raw\s*\(.*[%f"\+]|\.extra\s*\(
cursor\.execute.*format|cursor\.execute.*%

# File operations
send_file\s*\(|send_from_directory\s*\(|FileResponse\s*\(
open\s*\(.*request|os\.path\.join.*request
zipfile\.ZipFile.*extractall|tarfile\.open.*extractall

# SSRF
requests\.(get|post|put|delete|head)\s*\(.*request
urllib\.(request\.)?urlopen\s*\(|httpx\.(get|post)
aiohttp\.ClientSession

# XXE
etree\.(parse|fromstring)|xml\.dom\.minidom|xml\.sax
XMLParser|resolve_entities|defusedxml

# XSS
mark_safe\s*\(|\|safe\b|HttpResponse\s*\(.*request
Markup\s*\(

# Format string injection
\.format\s*\(.*request|%.*request\.(GET|POST|args)

# Weak random
\brandom\.(choice|randint|random)\s*\(

# Configuration security
DEBUG\s*=\s*True|SECRET_KEY\s*=\s*['"][^'"]{0,20}['"]
ALLOWED_HOSTS\s*=\s*\[.*\*

# Authorization checks
@login_required|@permission_required|IsAuthenticated
@app\.route.*methods.*DELETE|@router\.delete
```

---

## Audit Checklist

### Command Execution
- [ ] Search for `os.system` / `subprocess` (shell=True) / `os.popen`
- [ ] Verify subprocess arguments are lists, not strings
- [ ] Check `shlex.quote()` usage

### Code Execution
- [ ] Search for `eval` / `exec` / `compile` / `__import__`
- [ ] Check `getattr`/`setattr` dynamic call sources

### Deserialization
- [ ] Search for `pickle.load/loads` / `shelve.open` / `marshal.load` / `dill.load`
- [ ] Search for `yaml.load` and verify SafeLoader usage
- [ ] Search for `jsonpickle.decode`

### SSTI
- [ ] Search for `render_template_string` + user input concatenation
- [ ] Search for `Template()` directly using user input
- [ ] Check Mako/Tornado templates

### File Operations
- [ ] Check `send_file`/`FileResponse` path validation
- [ ] Search for `zipfile`/`tarfile` extraction operations (Zip Slip)
- [ ] Verify `secure_filename` usage (Flask)

### SQL Injection
- [ ] Search for `execute()` string concatenation (+, %, f"")
- [ ] Search for Django `raw()`/`extra()` concatenation
- [ ] Check `filter(**dict)` with controllable parameter names

### SSRF
- [ ] Search for `requests.get`/`urllib.urlopen` + user URL
- [ ] Check internal IP filtering (`ipaddress.is_private`)

### Format String
- [ ] Search for `.format(` + user input as template
- [ ] Check Django double formatting (% + format)

### Authorization Focus
- [ ] Check Flask view functions for `@login_required`
- [ ] Check Django CBVs for `LoginRequiredMixin`
- [ ] Compare permission consistency across CRUD methods
- [ ] Verify resource ownership checks (IDOR)

### Configuration Security
- [ ] `DEBUG = True` (production environment)
- [ ] `SECRET_KEY` strength
- [ ] `ALLOWED_HOSTS` configuration
- [ ] CSRF middleware enabled
