# File Operations Security Audit Module

> Scope: All projects involving file upload/download/read/write
> Related dimensions: D1 (Injection Vulnerabilities - Path Traversal), D5 (System Interaction Security)
> Loaded when file upload/download/read/write functionality is detected

## Audit Checklist

- [ ] Are file paths canonicalized (realpath/normalize) and verified to be within allowed directories
- [ ] Does file upload use magic bytes to verify type (not relying solely on file extension)
- [ ] Are uploaded filenames replaced with randomly generated names
- [ ] Is the upload directory outside the web root
- [ ] Is there a file size limit
- [ ] Does archive extraction check for symbolic links and path traversal (Zip Slip)
- [ ] Are temporary files created using secure functions (`mkstemp` instead of predictable paths)
- [ ] Does file download prevent path traversal
- [ ] Are file permissions correctly set (should not be world-writable)

## Framework/Language-Specific Pitfalls

- **Python os.path.join**: Discards the base directory prefix when encountering an absolute path argument
- **Node.js path.join**: Does not prevent `../` traversal; must use `path.resolve` + `startsWith` validation
- **Java**: Must use `Paths.get().normalize().toRealPath()` + `startsWith` validation
- **tarfile/zipfile**: `extractall()` does not check symbolic links or `../` paths by default; must validate members individually
- **File extension checks**: `evil.php.jpg`, null byte truncation (older versions) can bypass checks

## Grep Search Patterns

```
Grep: os\.path\.join|Path\.resolve|path\.join|Paths\.get
Grep: open\(|FileInputStream|fs\.readFile|fs\.createReadStream
Grep: sendFile|send_file|download|attachment
Grep: \.save\(|transferTo|write.*File|writeFile
Grep: upload|Upload|multipart|MultipartFile
Grep: \.filename|originalFilename|getOriginalFilename
Grep: tarfile|zipfile|ZipInputStream|unzip|extract
Grep: symlink|readlink|lstat|isSymbolicLink
Grep: mkstemp|mkdtemp|tmpfile|NamedTemporaryFile
Grep: content.type|Content-Type|mime|MIME
```

## Cross-References

- Related domain modules: domains/command-injection.md (filename injection into commands), domains/xss.md (SVG/HTML upload XSS), domains/race-conditions.md (TOCTOU)
