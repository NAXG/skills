# SSRF (Server-Side Request Forgery) Security Audit Module

> Scope: All projects with server-side HTTP request functionality
> Related dimensions: D1 (Injection Vulnerabilities), D5 (System Interaction Security)
> Loaded when server-side HTTP request functionality is detected

## Audit Checklist

- [ ] Do all outbound HTTP requests validate the target URL/IP
- [ ] Is IP validation performed at the socket layer after DNS resolution (DNS rebinding prevention)
- [ ] Are internal IP ranges blocked (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16)
- [ ] Are IPv6 loopback and private addresses blocked (`::1`, `::ffff:127.0.0.1`, `fc00::/7`)
- [ ] Are only http/https protocols allowed (blocking gopher/dict/file)
- [ ] Does the HTTP client disable automatic redirect following (or re-validate after redirect)
- [ ] Do Webhook/callback URLs have whitelist validation
- [ ] Do PDF generation, image preview, and similar features have SSRF protection
- [ ] Are cloud environment metadata endpoints (169.254.169.254) explicitly blocked

## Common Bypass Techniques (Verify During Defense Audit)

- **DNS rebinding**: First resolution passes validation, actual request DNS points to internal network
- **IPv6 mapping**: `[::ffff:127.0.0.1]`, `[0:0:0:0:0:ffff:7f00:1]`
- **IP encoding variants**: Hexadecimal `0x7f000001`, decimal `2130706433`, octal `0177.0.0.1`, shorthand `127.1`
- **URL parsing differences**: Userinfo segment `127.0.0.1@evil.com`, fragment truncation
- **Redirect bypass**: External URL returns 302 pointing to internal address
- **Protocol exploitation**: `gopher://` sending Redis commands, `file:///` reading local files

## Grep Search Patterns

```
Grep: requests\.(get|post|put|delete|head|patch)\(|urllib\.request\.urlopen
Grep: HttpURLConnection|HttpClient|OkHttpClient|RestTemplate|WebClient
Grep: http\.(Get|Post|Do)|net/http
Grep: fetch\(|axios\.(get|post)|got\(|node-fetch
Grep: curl_exec|file_get_contents\(.*http
Grep: webhook|callback.*url|notify.*url
Grep: ImageIO\.read\(.*URL|Image\.open\(.*requests
Grep: pdf.*url|render.*url|screenshot.*url
```

## Cross-References

- Related domain modules: domains/api-security.md (API outbound requests), domains/file-operations.md (file:// protocol)
- Related language modules: languages/python.md, languages/java.md, languages/go.md
