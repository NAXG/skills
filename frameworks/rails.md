# Rails Security Cheat Sheet

> Version scope: Rails 6.x/7.x/8.x | Load condition: Gemfile contains rails

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| .permit! allows all parameters | Mass Assignment | `params.permit!` |
| permit list too broad with :role/:is_admin | Privilege escalation | `permit(:role, :is_admin)` |
| skip_before_action :verify_authenticity_token | CSRF bypass | Skipped for entire controller |
| protect_from_forgery with: :null_session | Weakened CSRF | Confirm if API mode |
| YAML.load (Ruby<3.1) | Deserialization RCE | Not safe_load |
| Marshal.load with user input | Deserialization RCE | Direct deserialization |
| Kernel.open (Ruby<2.7) | Command execution | `open("#{params}")` supports pipes |
| Weak/leaked secret_key_base | Session forgery | Hardcoded short string |
| Login without reset_session | Session fixation | session[:user_id]= without prior reset |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `.where("...#{var}")` | SQL | String interpolation |
| `find_by_sql("...#{var}")` | SQL | Interpolation concatenation |
| `.order(params[:sort])` | SQL blind injection | ORDER BY CASE injection |
| `.pluck(params[:col])` | SQL | Controllable column name |
| `connection.execute("...#{var}")` | SQL | Direct execution |
| `system("...#{var}")` | Command injection | String interpolation |
| `` `...#{var}` `` (backticks) | Command injection | Same as above |
| `Open3.capture2("...#{var}")` | Command injection | Same as above |
| `render inline: params[:tpl]` | SSTI (Critical) | ERB code execution |
| `render file: params[:page]` | Arbitrary file read | Controllable path |
| `html_safe` / `raw` | XSS | Bypasses escaping |
| `redirect_to params[:url]` | Open redirect | Not validated |
| `Marshal.load(input)` | Deserialization RCE | Arbitrary objects |
| `YAML.load(input)` | Deserialization RCE | Psych<4.0 |

## Grep Search Patterns

```
# SQL injection
\.where\s*\(.*#\{|find_by_sql\s*\(.*#\{|\.order\s*\(params
\.execute\s*\(.*#\{|\.pluck\s*\(params|\.select\s*\(.*#\{

# Mass Assignment
\.permit!|params\[.*\]\.to_unsafe_h

# CSRF
skip_before_action.*verify_authenticity_token

# Deserialization
Marshal\.load|YAML\.load\s*\(|create_additions.*true

# Command injection
system\s*\(.*#\{|`.*#\{.*`|Open3.*#\{|IO\.popen.*#\{

# render injection
render\s+inline:|render\s+file:\s*params

# XSS
html_safe|\.raw\s

# Session
session\[:.*=(?!.*reset_session)

# Open redirect
redirect_to\s*params|redirect_to\s*.*request
```

## Audit Checklist

- [ ] Rails version and known CVEs
- [ ] where/find_by_sql string interpolation (SQL injection)
- [ ] order(params[]) ORDER BY injection
- [ ] .permit! and broad permit lists
- [ ] skip_before_action :verify_authenticity_token
- [ ] Marshal.load / YAML.load (deserialization)
- [ ] system/backticks/Open3 with interpolation (command injection)
- [ ] render inline/file with user input
- [ ] html_safe / raw with user input (XSS)
- [ ] reset_session call in login flow
- [ ] secret_key_base strength
- [ ] redirect_to params[] (open redirect)
- [ ] send_data/send_file filename source
