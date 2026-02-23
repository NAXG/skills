# PHP Security Audit

> PHP security audit module | See references/agent-contract.md for methodology
> Applicable to: PHP, Laravel, Symfony, WordPress, ThinkPHP

---

## Sources (User Input Points)

| Category | API |
|----------|-----|
| Superglobals | `$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`, `$_FILES`, `$_SERVER` |
| Input Stream | `file_get_contents('php://input')` |
| Server Variables | `$_SERVER['HTTP_*']`, `$_SERVER['PHP_SELF']`, `$_SERVER['REQUEST_URI']` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Code Execution | RCE | 94 | `eval`, `assert` (PHP<7.2), `create_function`, `preg_replace(/e)` |
| Command Execution | Command Injection | 78 | `system`, `exec`, `passthru`, `shell_exec`, `` ` `` , `popen`, `proc_open` |
| Callback Execution | RCE | 94 | `call_user_func`, `array_map`, `array_filter`, `usort` |
| SQL Execution | SQL Injection | 89 | `mysqli_query`, `->query()`, `DB::raw` |
| File Inclusion | LFI/RFI | 98 | `include`, `require`, `include_once`, `require_once` |
| Deserialization | RCE | 502 | `unserialize` |
| File Operations | Path Traversal | 22 | `file_get_contents`, `fopen`, `readfile`, `unlink` |
| File Write | WebShell | 94 | `file_put_contents`, `fwrite` |
| HTTP Requests | SSRF | 918 | `file_get_contents(http)`, `curl_exec`, `Guzzle` |

---

## PHP Specific Dangerous Patterns

### Variable Overwrite
```php
extract($_GET);          // registers GET params as variables, can overwrite $admin etc.
parse_str($query);       // same as above when no second parameter is provided
$$key = $value;          // foreach + variable variables
```

### Weak Type Comparison
```php
"0e123" == "0e456"       // true (both evaluate to 0 in scientific notation)
"1abc" == 1              // true
in_array("1abc", [0,1])  // true (no third parameter)
strcmp([], "password")   // 0 (array bypass)
```

### PHP Pseudo-Protocols
| Protocol | Purpose | Configuration Requirement |
|----------|---------|--------------------------|
| `php://filter` | Read source code (base64 encoded) | None |
| `php://input` | Read raw POST data | allow_url_include=On |
| `data://` | Data stream execution | allow_url_include=On |
| `phar://` | Trigger deserialization | None |

### Phar Deserialization (Often Overlooked)
The following functions can trigger deserialization when accepting the `phar://` protocol:
`file_exists`, `is_file`, `is_dir`, `filesize`, `file_get_contents`, `fopen`, `include`

### escapeshellarg + escapeshellcmd Combination Vulnerability
```php
$ep = escapeshellarg($param);    // '127.0.0.1'\'' -v -d a=1'
$eep = escapeshellcmd($ep);      // single quote escape, allows injection of extra arguments
```

### filter_var Bypass
```php
filter_var("javascript://alert(1)", FILTER_VALIDATE_URL);  // true
```

### Deserialization (Merged from php_deserialization.md)

Magic method trigger chain: `__wakeup` → `__destruct` → `__toString` → `__call` → `__get` → `__invoke`

CVE-2016-7124: When property count exceeds actual property count, `__wakeup` is skipped

---

## Grep Search Patterns

```regex
# Code execution
eval\s*\(|assert\s*\(|create_function\s*\(
preg_replace\s*\(.*\/.*e
call_user_func|array_map|array_filter|usort

# Command execution
system\s*\(|exec\s*\(|shell_exec\s*\(|passthru\s*\(
popen\s*\(|proc_open\s*\(|pcntl_exec\s*\(

# File inclusion
(include|require)(_once)?\s*\(\s*\$
php://|data://|phar://|zip://|expect://

# Deserialization
unserialize\s*\(|phar://
__wakeup|__destruct|__toString|__call|__get|__set
file_exists\s*\(.*phar|is_file\s*\(.*phar

# SQL injection
mysqli_query|mysql_query|pg_query
\$pdo->query.*\$|\$wpdb->query.*\$
DB::raw|whereRaw|selectRaw|orderByRaw|havingRaw
set\s+names\s+['"]gbk['"]

# File upload
move_uploaded_file|\$_FILES
\.php\d|\.phtml|\.phar|\.phps|\.inc

# File operations
unlink\s*\(|file_get_contents\s*\(|readfile\s*\(
file_put_contents\s*\(|fwrite\s*\(
\.\./|\.\.\\

# Variable overwrite
extract\s*\(\s*\$_|parse_str\s*\(.*\$_
foreach.*\$_.*\$\$

# Weak type
==\s*['"]0e|strcmp\s*\(.*\[
in_array\s*\(.*,.*\)\s*(?!,\s*true)

# XSS
echo\s+\$|print\s+\$|\<\?=\s*\$
\{!!.*!!\}

# SSTI
createTemplate|render_string|Twig_Environment
Smarty.*display.*string:

# HTTP response header injection
header\s*\(\s*["'].*\$|setcookie\s*\(\s*\$

# Open Redirect
header.*Location.*\$|redirect\s*\(\s*\$

# SSRF
curl_exec|file_get_contents\s*\(.*http
sprintf.*\$this->.*base|sprintf.*\$config.*url

# Configuration
disable_functions|open_basedir|display_errors
allow_url_include|allow_url_fopen

# Laravel
DB::raw|whereRaw|->raw\(
\$guarded\s*=\s*\[\s*\]|APP_DEBUG

# WordPress
\$wpdb->query|\$wpdb->get_results
wp_ajax_|current_user_can|check_ajax_referer

# ThinkPHP
think\\\\App|think\\\\Request|invokefunction

# ZIP Slip
ZipArchive|extractTo|extractPackage|PharData

# Indirect SSRF
sprintf.*\$this->.*base|sprintf.*\$config.*url
curl_setopt.*CURLOPT_URL.*\$this->
fixer::input.*url|fixer::input.*base
```

---

## Audit Checklist

### Code/Command Execution
- [ ] `eval`/`assert`/`create_function`/`preg_replace /e`
- [ ] `system`/`exec`/`shell_exec`/`passthru`/`popen`/`proc_open`
- [ ] Callback functions `call_user_func`/`array_map` with controllable parameters

### File Inclusion
- [ ] `include`/`require` + variables
- [ ] PHP pseudo-protocol usage (`php://filter`, `phar://`)
- [ ] `allow_url_include`/`allow_url_fopen` configuration

### Deserialization
- [ ] `unserialize` data source
- [ ] `phar://` trigger (file_exists/is_file etc.)
- [ ] Magic method chain audit

### SQL Injection
- [ ] Raw SQL concatenation / ORM raw methods
- [ ] Wide-byte injection (GBK encoding `set names 'gbk'`)
- [ ] Second-order injection scenarios

### File Operations
- [ ] `move_uploaded_file` file type/extension validation
- [ ] `unlink`/`readfile`/`file_put_contents` with controllable path
- [ ] ZIP extraction path traversal

### Variable Overwrite
- [ ] `extract($_GET/POST)` / `parse_str` without second parameter
- [ ] `foreach` + `$$` variable variables

### Weak Type
- [ ] `==` comparison (should use `===`)
- [ ] `in_array` without third parameter `true`

### Framework Specific
- [ ] Laravel: `DB::raw`/`whereRaw`, `{!! !!}`, `$guarded = []`, `APP_DEBUG`
- [ ] WordPress: `$wpdb->query` without `prepare`, `wp_ajax_` permission validation
- [ ] ThinkPHP: Version 5.x RCE (`invokefunction`)

### Logic Vulnerabilities
- [ ] `header('Location:')` missing `exit()` afterward
- [ ] Weak cookie validation (should validate session)
- [ ] Install lock file check without exit after detection

### Configuration
- [ ] `disable_functions` / `open_basedir`
- [ ] `display_errors` / `expose_php`
