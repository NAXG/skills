# .NET/C# Security Audit

> .NET/C# security audit module | See references/agent-contract.md for methodology
> Applicable to: ASP.NET Core, ASP.NET MVC, Blazor, WPF, .NET MAUI

---

## Sources (User Input Points)

| Category | API |
|----------|-----|
| Query Parameters | `Request.Query["name"]`, `[FromQuery]` |
| Request Body | `[FromBody]`, `Request.Body` |
| Route Parameters | `[FromRoute]`, `RouteData` |
| Headers/Cookies | `Request.Headers["X-Header"]`, `Request.Cookies["name"]` |
| File Uploads | `IFormFile`, `Request.Form.Files` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Deserialization | RCE | 502 | `BinaryFormatter`, `TypeNameHandling.All` |
| SQL Execution | SQL Injection | 89 | `SqlCommand`, `FromSqlRaw` |
| Command Execution | Command Injection | 78 | `Process.Start` |
| File Operations | Path Traversal | 22 | `File.Open`, `FileStream`, `Path.Combine` |
| HTTP Requests | SSRF | 918 | `HttpClient`, `WebClient` |
| XAML | RCE | - | `XamlReader.Load` |

---

## .NET Specific Dangerous Patterns

### BinaryFormatter (Extremely Dangerous, Deprecated in .NET 5+)
```csharp
BinaryFormatter formatter = new BinaryFormatter();
object obj = formatter.Deserialize(stream);  // RCE!
// 同样危险: SoapFormatter, NetDataContractSerializer, ObjectStateFormatter, LosFormatter
```

### Newtonsoft.Json TypeNameHandling
```csharp
var settings = new JsonSerializerSettings {
    TypeNameHandling = TypeNameHandling.All  // 危险! 允许 $type 指定类型
};
// TypeNameHandling.Auto / Objects 也危险
// 安全: TypeNameHandling.None (默认)
```

### Entity Framework Raw SQL
```csharp
// 危险
context.Users.FromSqlRaw($"SELECT * FROM Users WHERE Name = '{name}'");
context.Database.ExecuteSqlRaw($"DELETE FROM Users WHERE Id = {id}");

// 安全: FromSqlInterpolated 自动参数化
context.Users.FromSqlInterpolated($"SELECT * FROM Users WHERE Name = {name}");
```

### Path.Combine Does Not Prevent Path Traversal
```csharp
Path.Combine("uploads", "../../etc/passwd")  // = "../../etc/passwd"
// 如果第二参数是绝对路径，直接返回第二参数
Path.Combine("uploads", "/etc/passwd")  // = "/etc/passwd"
```

### ViewState Deserialization (ASP.NET WebForms)
```csharp
// machineKey 泄露 → ViewState 反序列化 RCE
// 检查 web.config 中的 machineKey 配置
```

### Razor View XSS
```csharp
@Html.Raw(userInput)  // 危险: 不转义
@userInput            // 安全: 自动转义
```

---

## Grep Search Patterns

```regex
# Deserialization
BinaryFormatter|SoapFormatter|NetDataContractSerializer
ObjectStateFormatter|LosFormatter|XamlReader\.Load
TypeNameHandling\.(All|Auto|Objects)
JsonSerializerSettings|TypeNameAssemblyFormat

# SQL injection
SqlCommand|ExecuteReader|ExecuteNonQuery|ExecuteScalar
FromSqlRaw|ExecuteSqlRaw
string\.Format.*SELECT|\$".*SELECT|"\s*\+\s*".*WHERE
Query<|Execute\(  # Dapper

# Command execution
Process\.Start|ProcessStartInfo|cmd\.exe|/bin/bash
PowerShell|Invoke-Expression

# Path traversal
Path\.Combine|File\.(Open|Read|Write|Delete)|FileStream
IFormFile|SaveAs|CopyTo
\.\.\\\\|\.\.\/

# SSRF
HttpClient|WebClient|WebRequest|HttpWebRequest
GetAsync|PostAsync|SendAsync

# XSS
Html\.Raw\s*\(|@Html\.Raw
HtmlString\s*\(|MarkupString

# XML
XmlDocument|XmlReader|XmlTextReader
XmlReaderSettings|DtdProcessing|ProhibitDtd

# CSRF
[ValidateAntiForgeryToken]|AntiForgery
IgnoreAntiforgeryToken

# Authentication/Authorization
\[Authorize\]|\[AllowAnonymous\]
\[Authorize\(Roles|Policy\)
AddAuthentication|AddAuthorization

# Configuration security
ConnectionString|appsettings.*json
(password|secret|key)\s*[:=]\s*"[^"]*"
ASPNETCORE_ENVIRONMENT|Development

# CORS
AddCors|WithOrigins|AllowAnyOrigin
AllowCredentials.*AllowAnyOrigin

# Entity Framework
FromSqlRaw|ExecuteSqlRaw|SqlQuery
\.Include\(|\.ThenInclude\(

# Blazor
@((MarkupString)|Html\.Raw)
JSRuntime|InvokeAsync

# Race conditions
static\s+(readonly\s+)?(?!.*readonly).*=.*new
ConcurrentDictionary|ConcurrentBag|SemaphoreSlim
lock\s*\(|Monitor\.(Enter|Exit)
```

---

## Dangerous Dependencies Quick Reference

| Dependency | Risk | Version |
|------------|------|---------|
| Newtonsoft.Json (TypeNameHandling) | Deserialization RCE | Configuration issue |
| System.Runtime.Serialization (BinaryFormatter) | RCE | Deprecated in .NET 5+ |
| ysoserial.net Gadgets | TypeConfuseDelegate, TextFormattingRunProperties, PSObject | - |

---

## Audit Checklist

### Deserialization
- [ ] `BinaryFormatter` / `SoapFormatter` / `NetDataContractSerializer`
- [ ] `TypeNameHandling` not set to None
- [ ] `XamlReader.Load`
- [ ] ViewState + machineKey leakage

### SQL Injection
- [ ] `SqlCommand` string concatenation
- [ ] `FromSqlRaw` / `ExecuteSqlRaw` + concatenation (should use FromSqlInterpolated)
- [ ] Dapper `Query<>` / `Execute` + concatenation

### Command Execution
- [ ] `Process.Start` with controllable parameters
- [ ] PowerShell invocations

### File Operations
- [ ] `Path.Combine` + user input (absolute path override)
- [ ] `IFormFile` type/size validation
- [ ] Path traversal checks

### XSS
- [ ] `@Html.Raw` usage
- [ ] Blazor `MarkupString`

### Authorization Focus
- [ ] Controller/Action has `[Authorize]`
- [ ] `[AllowAnonymous]` overuse
- [ ] Resource ownership validation

### Configuration Security
- [ ] `appsettings.json` hardcoded credentials
- [ ] CORS AllowAnyOrigin + AllowCredentials
- [ ] CSRF `[ValidateAntiForgeryToken]`
- [ ] Development environment configuration leakage
