# Pattern Library Routing

> Loading route table for language/framework/domain modules. Used in Phase 1~3.

## 1) Layered Loading Strategy

- Layer A (Framework layer, on-demand): `frameworks/*.md`
- Layer B (Language-specific layer, on-demand): `languages/*.md`

Goal: First use the framework layer to determine boundaries, then use the language-specific layer for validation and gap filling, avoiding loading too much material at once.

## 2) Framework Routing

Load after identifying frameworks from dependency files, directory structure, and annotation/middleware signatures.

### Canonical ID Mapping

| Canonical ID | Module File | Identification Signatures (Examples) |
|---|---|---|
| `spring` | `frameworks/spring.md` | `spring-boot-starter`, `@RestController` |
| `mybatis` | `frameworks/mybatis_security.md` | `mybatis`, `@Mapper` |
| `java-web` | `frameworks/java_web_framework.md` | Servlet, JSP, Struts |
| `django` | `frameworks/django.md` | `Django==`, `urlpatterns` |
| `flask` | `frameworks/flask.md` | `Flask`, `@app.route` |
| `fastapi` | `frameworks/fastapi.md` | `fastapi`, `@app.get` |
| `gin` | `frameworks/gin.md` | `gin-gonic/gin`, `gin.Default()` |
| `express` | `frameworks/express.md` | `"express":`, `app.use(` |
| `koa` | `frameworks/koa.md` | `koa`, `ctx.body` |
| `nest-fastify` | `frameworks/nest_fastify.md` | `@nestjs/core`, `fastify` |
| `laravel` | `frameworks/laravel.md` | `laravel/framework`, `Route::` |
| `rails` | `frameworks/rails.md` | `gem "rails"`, `before_action` |
| `dotnet` | `frameworks/dotnet.md` | `Microsoft.AspNetCore`, `[ApiController]` |
| `rust-web` | `frameworks/rust_web.md` | Actix/Axum/Rocket |

### Confidence Rules

- `high`: Both dependency evidence and code evidence match
- `medium`: Either dependency or code matches alone, with strong signatures
- `low`: Only weak signatures match, no key API/dependency corroboration

### Selection Rules

- `loaded_framework_modules` selects only from `framework_candidates`
- Each round prioritizes top 1-2 with `high/medium`
- `low` is not loaded by default, unless the candidate is on a high-risk data flow main path

## 3) Language-Specific Routing

Main modules per language (always loaded):

| Language | Main Module |
|----------|------------|
| Java | `languages/java.md` |
| Python | `languages/python.md` |
| PHP | `languages/php.md` |
| Go | `languages/go.md` |
| JavaScript/Node.js | `languages/javascript.md` |
| C#/.NET | `languages/dotnet.md` |
| C/C++ | `languages/c_cpp.md` |
| Ruby | `languages/ruby.md` |
| Rust | `languages/rust.md` |

### Java Advanced Module Loading Rules

`languages/java-advanced.md` covers deserialization/JNDI/XXE/script engine/Fastjson/advanced practical patterns.

**Loading conditions** (load if any is met):
- ObjectInputStream / readObject / Serializable detected
- InitialContext / lookup / JNDI configuration detected
- XML parser detected (DocumentBuilder / SAXParser)
- ScriptEngine / Nashorn detected
- com.alibaba.fastjson dependency detected
- deep mode auto-loads

## 4) Budget and Gates

- Max `2` framework modules per round (sorted by attack surface priority)
- Max `2` language-specific modules per round (only for hot dimensions)
- Do not enter language-specific topics unless `Critical/High` clues are present
- After entering Phase 3, a "1 framework + 1 language-specific topic" combination verification is allowed
- After loading, must annotate in the report: `loaded_framework_modules`, `loaded_language_modules`

## 5) Quick Decision Template

```text
if language identified:
  load languages/<language>.md

if framework identified:
  load top-1~2 frameworks/*.md by risk and exposure

if high-risk path unresolved or bypass validation needed:
  load top-1~2 languages/*.md for that dimension
```

## 6) Domain Module Routing

Domain modules are loaded on-demand under the following conditions:

| Domain Module | Loading Condition |
|---------------|-------------------|
| sql-injection.md | Database dependency or SQL-related Sink detected |
| command-injection.md | exec/system/popen-type Sink detected |
| xss.md | Web frontend rendering or template engine detected |
| authentication.md | Login/registration/password-related functionality detected |
| authorization.md | Role/permission/access control-related functionality detected |
| file-operations.md | File upload/download/read-write functionality detected |
| ssrf.md | Server-side HTTP request functionality detected |
| deserialization.md | Deserialization Sink detected |
| api-security.md | REST/GraphQL/gRPC API detected |
| cryptography.md | Encryption/signing/hashing operations detected |
| llm-security.md | LLM/AI-related dependency detected |
| race-conditions.md | Concurrency/multi-threading/coroutine patterns detected |

> Generic vulnerability patterns in framework/language modules should reference the corresponding domain module, retaining only framework-specific variants and API call patterns.

### Domain Module Budget

- Max `3` domain modules per round (sorted by attack surface priority)
- Domain modules share the loading budget with framework/language modules, total not exceeding `5` modules/round
- After loading, must annotate in the report: `loaded_domain_modules`
