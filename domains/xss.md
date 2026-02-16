# XSS (Cross-Site Scripting) Security Audit Module

> Scope: All web frontend rendering and template engine projects
> Related dimensions: D1 (Injection Vulnerabilities), D4 (Output Encoding Security)
> Loaded when web frontend rendering or template engines are detected

## Audit Checklist

- [ ] Does the template engine enable auto-escaping by default
- [ ] Are there unescaped outputs such as `|safe`, `<%- %>`, `{!! !!}`, `v-html`, `dangerouslySetInnerHTML`
- [ ] Does JavaScript use `innerHTML`, `outerHTML`, `document.write()` with user data
- [ ] Are URL parameters directly reflected onto the page
- [ ] Are `javascript:` and `data:` URI schemes filtered
- [ ] Are uploaded SVG files parsed as HTML
- [ ] Is the Content-Security-Policy header configured
- [ ] Is rich text editor output sanitized via HTML cleaning (allowlist approach)
- [ ] Does `postMessage` validate `origin`
- [ ] Is the JSON API response Content-Type set to `application/json`

## Framework/Template Engine-Specific Pitfalls

- **Jinja2**: `|safe` and `Markup()` disable auto-escaping
- **EJS**: `<%-` does not escape, `<%=` does escape
- **JSP**: `<%= %>` and `${param.x}` do not escape; use `<c:out>` or `fn:escapeXml`
- **Laravel Blade**: `{!! !!}` does not escape, `{{ }}` does escape
- **React**: `dangerouslySetInnerHTML` bypasses default protection
- **Vue**: `v-html` bypasses default protection
- **Angular**: `[innerHTML]` goes through the built-in sanitizer, but `bypassSecurityTrust*` series bypasses it

## Grep Search Patterns

```
Grep: innerHTML|outerHTML|document\.write|document\.writeln
Grep: \|safe|markSafe|mark_safe|Markup\(|SafeString
Grep: <%[-=]|<c:out|fn:escapeXml
Grep: v-html|dangerouslySetInnerHTML|\[innerHTML\]
Grep: DOMPurify|sanitize|bleach\.clean|Sanitize
Grep: eval\(|setTimeout\(.*['\"]|setInterval\(.*['\"]
Grep: \.html\(|\.append\(.*<|\.prepend\(.*<
Grep: postMessage|addEventListener.*message
Grep: location\.hash|location\.search|document\.referrer
Grep: Content-Security-Policy|CSP
```

## Cross-References

- Related domain modules: domains/api-security.md (API response security), domains/authentication.md (session hijacking)
- Related language modules: languages/javascript.md (DOM API)
