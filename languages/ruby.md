# Ruby/Rails Security Audit

> Ruby/Rails security audit module | See references/agent-contract.md for methodology
> Applicable to: Ruby on Rails, Sinatra, Hanami

---

## Sources (User Input Points)

| Framework | API |
|-----------|-----|
| Rails | `params[:name]`, `request.headers["X-Header"]`, `cookies[:session]`, `request.body` |
| Sinatra | `params[:name]`, `request.env["HTTP_X_HEADER"]` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Command Execution | Command Injection | 78 | `` `cmd` ``, `system`, `exec`, `%x()`, `Open3`, `IO.popen` |
| Code Execution | Code Injection | 94 | `eval`, `instance_eval`, `class_eval`, `send` |
| SQL Execution | SQL Injection | 89 | `where("... #{}")`, `find_by_sql`, `order()` |
| Deserialization | RCE | 502 | `Marshal.load`, `YAML.load`, `Oj.load` |
| File Operations | Path Traversal | 22 | `send_file`, `File.read`, `IO.read` |
| HTTP Requests | SSRF | 918 | `Net::HTTP`, `open-uri`, `HTTParty`, `Faraday` |
| Template Injection | SSTI | 97 | `ERB.new(input).result` |
| XSS | XSS | 79 | `raw`, `html_safe`, `<%==` |

---

## Ruby/Rails Specific Dangerous Patterns

### send / public_send Dynamic Method Invocation
```ruby
# Dangerous: user-controllable method name
object.send(params[:method], params[:arg])  # can call any method including private
object.public_send(params[:method])         # slightly safer but can still call system etc.
```

### ERB Template Injection
```ruby
# Dangerous: user input used as template
ERB.new(user_input).result(binding)  # RCE! binding exposes context
```

### YAML.load (Unsafe by Default in Ruby < 3.1)
```ruby
YAML.load(data)       # Dangerous: allows arbitrary object instantiation
YAML.safe_load(data)  # Safe: only allows basic types
# Ruby 3.1+ YAML.load defaults to safe_load behavior
```

### Rails SQL Injection Hidden Spots
```ruby
# Dangerous: order/pluck/reorder accept strings
User.order(params[:sort])              # SQL injection
User.where("name LIKE '%#{q}%'")       # string interpolation
User.find_by_sql("SELECT * FROM users WHERE id = #{id}")

# Safe
User.order(Arel.sql(sanitized))  # but Arel.sql itself does not sanitize
User.where("name LIKE ?", "%#{q}%")
```

### html_safe / raw XSS
```ruby
# Dangerous: marks string as safe, bypassing Rails auto-escaping
raw(user_input)               # XSS
user_input.html_safe          # XSS
content_tag(:div, user_input.html_safe)

# In ERB
<%= raw @user_input %>        # XSS
<%== @user_input %>           # XSS (equivalent to raw)
```

### Mass Assignment
```ruby
# Dangerous: permit is too permissive
params.require(:user).permit!  # allows all parameters
params.require(:user).permit(:name, :email, :admin)  # admin can be tampered with

# Safe: only allow necessary fields
params.require(:user).permit(:name, :email)
```

---

## Grep Search Patterns

```regex
# Command execution
\bsystem\s*\(|`[^`]*\#\{|\bexec\s*\(|%x\(|%x\{
IO\.popen|Open3\.(capture|popen|pipeline)
Kernel\.(system|exec|spawn)|Shellwords

# Code execution
\beval\s*\(|instance_eval|class_eval|module_eval
send\s*\(|public_send\s*\(|__send__\s*\(
constantize|const_get

# SQL injection
\.where\s*\(["'].*\#\{|\.order\s*\(.*params
find_by_sql|\.pluck\s*\(.*params|\.reorder\s*\(.*params
\.select\s*\(["'].*\#\{|\.group\s*\(.*params
\.having\s*\(["'].*\#\{|\.joins\s*\(["'].*\#\{
Arel\.sql\s*\(

# Deserialization
Marshal\.load|Marshal\.restore
YAML\.load\s*\((?!.*safe)|YAML\.unsafe_load
Oj\.load\s*\((?!.*mode.*:strict)

# File operations
send_file\s*\(|File\.(read|write|open|delete)|IO\.(read|write)
FileUtils\.(cp|mv|rm|ln)

# XSS
\.html_safe|raw\s*\(|<%==
content_tag.*html_safe

# Template injection
ERB\.new\s*\(.*\)\.result|Erubis|Slim::Template

# SSRF
Net::HTTP|URI\.(parse|open)|open-uri|HTTParty
Faraday|RestClient|Typhoeus

# Mass Assignment
\.permit!|\.permit\(.*:admin|\.permit\(.*:role

# Authentication/Authorization
before_action.*authenticate|skip_before_action.*authenticate
authorize!|can\?|CanCanCan|Pundit
current_user

# Configuration security
secret_key_base|Rails\.application\.secrets
config\.force_ssl|protect_from_forgery

# Session
session\[|cookies\[|reset_session
cookie_store|session_store

# Dependency security
Gemfile\.lock|bundler-audit|brakeman

# Hardcoded credentials
(password|secret|token|api_key)\s*[:=]\s*['"][^'"]+['"]

# CORS
rack-cors|allow_origin
```

---

## Dangerous Dependencies Quick Reference

| Gem | Risk | Detection |
|-----|------|-----------|
| Rails < 7.0 | Multiple known CVEs | `rails.*version` |
| nokogiri < 1.13 | XXE/XSS | `nokogiri.*version` |
| devise < 4.8 | Authentication bypass | `devise.*version` |
| activerecord (all versions) | SQL injection (improper usage) | `.where` string interpolation |

---

## Audit Checklist

### Command Execution
- [ ] `` ` `` / `system` / `exec` / `%x()` / `IO.popen` / `Open3`
- [ ] `Kernel.spawn` with controllable parameters

### Code Execution
- [ ] `eval` / `instance_eval` / `class_eval`
- [ ] `send` / `public_send` + user-controllable method name
- [ ] `constantize` / `const_get` + user input

### SQL Injection
- [ ] `.where("... #{}")` string interpolation
- [ ] `.order(params[:sort])` controllable sort field
- [ ] `find_by_sql` / `Arel.sql` concatenation

### Deserialization
- [ ] `Marshal.load` data source
- [ ] `YAML.load` (should use `safe_load`)
- [ ] `Oj.load` mode is strict

### XSS
- [ ] `raw` / `html_safe` / `<%==` usage
- [ ] `content_tag` + html_safe

### Authorization Focus
- [ ] `before_action :authenticate_user!` covers all controllers
- [ ] `skip_before_action` overuse
- [ ] CanCanCan/Pundit policy completeness
- [ ] Mass Assignment: `permit!` or overly broad permit

### Configuration Security
- [ ] `secret_key_base` strength
- [ ] `force_ssl` enabled
- [ ] `protect_from_forgery` CSRF protection
- [ ] Bundler-audit dependency check
