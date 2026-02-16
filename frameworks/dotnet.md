# ASP.NET Core Security Cheat Sheet

> Version scope: ASP.NET Core 6/7/8, Blazor, Minimal APIs | Load condition: .csproj contains Microsoft.AspNetCore

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| [IgnoreAntiforgeryToken] | CSRF bypass | State-modifying endpoint skips validation |
| [AllowAnonymous] overrides [Authorize] | Authentication bypass | Annotated on sensitive actions |
| Minimal API without RequireAuthorization | Authentication bypass | `MapGet/MapPost` without authorization |
| FallbackPolicy not set | Default allows anonymous | Unannotated endpoints accessible |
| TypeNameHandling.All/Auto | Deserialization RCE | Newtonsoft.Json configuration |
| BinaryFormatter | Deserialization RCE | Deprecated but still used in legacy code |
| AllowAnyOrigin + AllowCredentials | CORS configuration conflict | Credential theft |
| SetIsOriginAllowed(_ => true) | CORS wide open | Dynamically allows all origins |
| UseDeveloperExceptionPage in production | Information disclosure | Stack trace/source code leakage |
| Blazor MarkupString | XSS | Equivalent to Html.Raw |
| Hardcoded keys in appsettings.json | Credential leakage | ConnectionStrings with passwords |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `FromSqlRaw("..." + var)` | SQL | EF Core raw concatenation |
| `ExecuteSqlRaw("..." + var)` | SQL | EF Core execute concatenation |
| `connection.Query("..." + var)` | SQL | Dapper concatenation |
| `new SqlCommand("..." + var)` | SQL | ADO.NET concatenation |
| `Html.Raw(userInput)` | XSS | Razor unescaped |
| `(MarkupString)userInput` | XSS | Blazor unescaped |
| `PhysicalFile(path + var)` | Path traversal | File download |
| `BinaryFormatter.Deserialize()` | Deserialization RCE | |
| `TypeNameHandling.All` | Deserialization RCE | Newtonsoft polymorphic |

## Grep Search Patterns

```
# SQL injection
FromSqlRaw\s*\(.*\+|ExecuteSqlRaw\s*\(.*\+|SqlCommand\s*\(.*\+
connection\.(Query|Execute)\s*\(.*\+

# XSS
Html\.Raw\s*\(|MarkupString\)

# CSRF
\[IgnoreAntiforgeryToken\]

# Authorization
\[AllowAnonymous\]
MapGet\(|MapPost\(|MapPut\(|MapDelete\(

# Deserialization
BinaryFormatter|TypeNameHandling\.(All|Auto|Objects)
NetDataContractSerializer|LosFormatter

# Path traversal
PhysicalFile\s*\(.*\+|Path\.Combine\s*\(.*fileName

# CORS
AllowAnyOrigin|SetIsOriginAllowed.*true

# Sensitive configuration
"ConnectionStrings".*password|appsettings.*Development.*json
```

## Audit Checklist

- [ ] ASP.NET Core version and known CVEs
- [ ] FromSqlRaw/ExecuteSqlRaw string concatenation
- [ ] Dapper Query/Execute concatenation
- [ ] Html.Raw / MarkupString (XSS)
- [ ] [IgnoreAntiforgeryToken] (CSRF bypass)
- [ ] [AllowAnonymous] on sensitive Controllers
- [ ] FallbackPolicy authorization configuration
- [ ] Minimal API endpoint RequireAuthorization
- [ ] BinaryFormatter / TypeNameHandling (deserialization)
- [ ] File download path validation
- [ ] CORS AllowAnyOrigin / SetIsOriginAllowed
- [ ] Hardcoded keys in appsettings.json
- [ ] Blazor MarkupString and JS Interop
- [ ] UseDeveloperExceptionPage environment check
