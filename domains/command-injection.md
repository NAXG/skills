# Command Injection Security Audit Module

> Scope: All projects that execute system commands
> Related dimensions: D1 (Injection Vulnerabilities), D5 (System Interaction Security)
> Loaded when exec/system/popen type sinks are detected

## Audit Checklist

- [ ] Are there `shell=True` (Python) or `sh -c` (Java/Go) calls
- [ ] Are system commands concatenated with user input
- [ ] Can library functions replace command-line calls (e.g., use `socket` instead of `ping`)
- [ ] Does input validation use a whitelist (not blacklist filtering of metacharacters)
- [ ] Does the array parameter form still have argument injection risks (`--checkpoint-action`, etc.)
- [ ] Are filenames/paths used directly as command arguments
- [ ] Can command fields in configuration files/databases be modified by users
- [ ] Does command execution follow the principle of least privilege

## Framework/Language-Specific Pitfalls

- **Python**: `subprocess.call(shell=True)` is dangerous; array form `["cmd", arg]` is safe; `shlex.quote()` for cases where shell is required
- **Java**: `Runtime.exec(String)` single-string form is parsed by the shell; `ProcessBuilder("sh","-c",cmd)` is equally dangerous
- **Node.js**: `child_process.exec()` uses the shell; `execFile()`/`spawn()` do not go through the shell
- **Argument injection**: Even with the array form, `--` prefixed arguments can still be injected (e.g., tar `--checkpoint-action`, curl `-o`); use `--` to terminate option parsing

## Grep Search Patterns

```
Grep: os\.system\(|os\.popen\(|subprocess\.(call|run|Popen|check_output)\(
Grep: shell\s*=\s*True
Grep: Runtime\.getRuntime\(\)\.exec|ProcessBuilder
Grep: child_process|\.exec\(|\.execSync\(|\.spawn\(
Grep: exec\.Command\(|exec\.CommandContext\(
Grep: system\(|popen\(|shell_exec\(|passthru\(|proc_open\(
Grep: backtick|%x\[|IO\.popen|Kernel\.system
```

## Cross-References

- Related domain modules: domains/file-operations.md (filename injection), domains/api-security.md (API input validation)
- Related language modules: languages/python.md, languages/java.md, languages/javascript.md, languages/go.md
