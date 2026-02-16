# JavaScript/Node.js Security Audit

> JavaScript/Node.js security audit module | See references/agent-contract.md for methodology
> Applicable to: Express, Koa, Fastify, Next.js, Nest.js

---

## Sources (User Input Points)

| Framework | API |
|-----------|-----|
| Express | `req.query`, `req.body`, `req.params`, `req.headers`, `req.cookies`, `req.files` |
| Koa | `ctx.query`, `ctx.request.body`, `ctx.params`, `ctx.headers`, `ctx.cookies` |
| Fastify | `request.query`, `request.body`, `request.params`, `request.headers` |

## Sinks (Dangerous Functions)

| Sink Type | Vulnerability | CWE | Dangerous Functions |
|-----------|--------------|-----|---------------------|
| Code Execution | Code Injection | 94 | `eval`, `Function()`, `vm.run*`, `setTimeout/setInterval` (string) |
| Command Execution | Command Injection | 78 | `child_process.exec`, `shelljs.exec` |
| SQL Execution | SQL Injection | 89 | `connection.query` (concatenation) |
| File Operations | Path Traversal | 22 | `fs.readFile`, `fs.writeFile`, `res.sendFile` |
| Prototype Pollution | Prototype Pollution | 1321 | `Object.assign`, `_.merge`, `$.extend` |
| NoSQL Injection | NoSQL Injection | 943 | `collection.find({user: req.body.user})` |
| Template Injection | SSTI | 97 | `ejs.render`, `pug.render`, `nunjucks.renderString` |

---

## JavaScript/Node.js Specific Dangerous Patterns

### Prototype Pollution
```javascript
// 危险: 递归合并用户输入到对象
_.merge(target, userInput)     // {"__proto__": {"isAdmin": true}}
Object.assign(target, source)  // 浅拷贝也可污染
$.extend(true, target, source) // jQuery 深拷贝

// 危险: 自定义 merge 未过滤 __proto__/constructor
for (let key in source) { target[key] = source[key]; }
```

### NoSQL Injection (MongoDB)
```javascript
// 危险: 直接将 req.body 作为查询条件
User.find({ user: req.body.user, pass: req.body.pass })
// 攻击: {"user":"admin","pass":{"$ne":""}} → 绕过密码

// 危险: $where 运算符
User.find({ $where: "this.name == '" + name + "'" })
```

### ReDoS (Regular Expression Denial of Service)
```javascript
// 危险模式: 嵌套量词 + 回溯
/(a+)+$/        // 指数级回溯
/([a-zA-Z]+)*$/ // 同上
/(a|a)*$/       // 交替 + 重复
```

### Unsafe require/import
```javascript
// 危险: 动态 require 用户输入
require(req.query.module)   // 任意模块加载
import(userInput)           // 动态 import
```

---

## Grep Search Patterns

```regex
# Code execution
\beval\s*\(|\bFunction\s*\(|vm\.(runInNewContext|runInThisContext|compileFunction)
setTimeout\s*\([^,)]*[\+`]|setInterval\s*\([^,)]*[\+`]
new Function\s*\(

# Command execution
child_process\.(exec|execSync|spawn|execFile|fork)
shelljs.*exec|sh\.exec
shell\s*:\s*true

# Prototype pollution
(Object\.assign|_\.merge|_\.mergeWith|_\.set|_\.defaultsDeep|\$\.extend)\s*\(
__proto__|constructor\.prototype
for\s*\(\s*(let|var|const)\s+\w+\s+in

# NoSQL injection
\$where|\$ne|\$gt|\$lt|\$regex|\$in|\$nin
collection\.(find|findOne|update|delete)\s*\(.*req\.(body|query|params)
\.find\s*\(\s*\{.*req\.|\.findOne\s*\(\s*\{.*req\.

# SQL injection
\.query\s*\(`.*\$\{|\.query\s*\(.*\+
mysql\.format|knex\.raw

# Path traversal
fs\.(readFile|writeFile|readFileSync|readdir|unlink|createReadStream|createWriteStream)
res\.(sendFile|download)\s*\(|require\s*\(.*req\.
path\.join\s*\(.*req\.(query|body|params)

# ReDoS
/\([^)]*\+\)\+/|/\([^)]*\*\)\*/|/\([^)]*\+\)\*/
safe-regex|re2

# XSS
\.innerHTML\s*=|\.outerHTML\s*=|document\.write\s*\(
dangerouslySetInnerHTML|v-html
res\.(send|write)\s*\(.*req\.(query|body|params)

# SSRF
(axios|node-fetch|got|request|superagent|http\.get|https\.get)\s*\(
url\.parse|new URL\s*\(.*req\.

# Template injection
ejs\.render\s*\(|pug\.render\s*\(|nunjucks\.renderString
handlebars\.compile\s*\(.*req|Mustache\.render\s*\(.*req

# Insecure deserialization
JSON\.parse\s*\(.*req|node-serialize|funcster|serialize-javascript

# JWT
jsonwebtoken|algorithms.*none|verify\s*=\s*false

# CORS
Access-Control-Allow-Origin.*\*|cors\(\s*\{.*origin.*true

# Sensitive information
(password|secret|token|api_key|apikey)\s*[:=]\s*['"][^'"]+['"]
\.env|process\.env

# Express security
helmet|csurf|express-rate-limit
trust\s*proxy|x-powered-by

# Dependency security
npm audit|snyk|node_modules
```

---

## Dangerous Dependencies Quick Reference

| Dependency | Risk | Detection |
|------------|------|-----------|
| lodash < 4.17.21 | Prototype pollution (_.merge) | `lodash.*version` |
| express-fileupload < 1.3.1 | Prototype pollution | `express-fileupload.*version` |
| node-serialize | Arbitrary code execution | `node-serialize` |
| ejs < 3.1.7 | SSTI/RCE | `ejs.*version` |
| jsonwebtoken < 9.0.0 | Algorithm confusion | `jsonwebtoken.*version` |
| minimist < 1.2.6 | Prototype pollution | `minimist.*version` |

---

## Audit Checklist

### Code/Command Execution
- [ ] `eval`/`Function()`/`vm.run*`/dynamic `require`
- [ ] `child_process.exec`/`spawn(shell:true)`
- [ ] `setTimeout`/`setInterval` with string arguments

### Prototype Pollution
- [ ] `_.merge`/`Object.assign`/`$.extend` + user input
- [ ] Custom merge/deepCopy filtering `__proto__`/`constructor`
- [ ] lodash version check

### NoSQL Injection
- [ ] MongoDB `find`/`findOne` directly using `req.body`
- [ ] `$where`/`$ne`/`$gt` operator injection
- [ ] Input type validation (should ensure string, not object)

### Path Traversal
- [ ] `fs.*`/`res.sendFile`/`res.download` + user path
- [ ] `path.join` prefix validation

### ReDoS
- [ ] User input passed to regex matching
- [ ] Nested quantifier patterns

### XSS
- [ ] `innerHTML`/`document.write`/`v-html`/`dangerouslySetInnerHTML`
- [ ] `res.send` directly outputting user input

### Authorization Focus
- [ ] Express route middleware chain check
- [ ] DELETE/PUT route permission validation
- [ ] JWT algorithm verification (disallow none)

### Configuration Security
- [ ] Helmet enabled
- [ ] CORS configuration
- [ ] CSRF protection
- [ ] `.env` file not in version control
