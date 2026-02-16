# Java Advanced Security - Deserialization/JNDI/XXE/Script Engines

---

## 1. Deserialization

### Entry Points

| Type | Sink Functions | Detection Regex |
|------|---------------|-----------------|
| Java Native | `ObjectInputStream.readObject()` / `readUnshared()` | `ObjectInputStream\|readObject\|readUnshared` |
| Fastjson | `JSON.parseObject()` / `JSON.parse()` | `JSON\.parse\|JSON\.parseObject` |
| Jackson | `ObjectMapper.readValue()` (enableDefaultTyping) | `enableDefaultTyping\|readValue` |
| XStream | `XStream.fromXML()` | `XStream\|fromXML` |
| SnakeYAML | `Yaml.load()` (not loadAs SafeConstructor) | `Yaml\.load\|new Yaml\(` |
| XMLDecoder | `XMLDecoder.readObject()` | `XMLDecoder` |

### Core Gadget Chain Quick Reference

| Chain Name | Dependency | Version Restrictions | Trigger Method |
|------------|-----------|---------------------|----------------|
| CC1 | commons-collections 3.x | JDK < 8u71 | LazyMap + InvokerTransformer |
| CC2 | commons-collections4 4.0 | None | PriorityQueue + TransformingComparator |
| CC3 | commons-collections 3.x | JDK < 8u71 | TrAXFilter + TemplatesImpl |
| CC5 | commons-collections 3.x | JDK >= 8u76 | BadAttributeValueExpException |
| CC6 | commons-collections 3.x | No JDK restriction | HashSet + TiedMapEntry |
| CC7 | commons-collections 3.x | No JDK restriction | Hashtable + LazyMap |
| CB1 | commons-beanutils 1.x | None | BeanComparator + TemplatesImpl |
| Spring1 | spring-core | None | MethodInvokeTypeProvider |
| JDK7u21 | JDK 7u21- | Specific JDK only | AnnotationInvocationHandler |
| C3P0-JNDI | c3p0 | None | JndiRefForwardingDataSource |

### Gadget Chain Detection Regex

```regex
# Transformer chains
ChainedTransformer|InvokerTransformer|ConstantTransformer|LazyMap\.decorate

# BeanUtils
BeanComparator|PropertyUtils\.getProperty

# TemplatesImpl (bytecode execution)
TemplatesImpl|_bytecodes|newTransformer|getOutputProperties

# C3P0
JndiRefForwardingDataSource|PoolBackedDataSource|C3P0DataSource

# Spring
MethodInvokeTypeProvider|ObjectFactoryDelegatingInvocationHandler
```

### Defense Configuration

```java
// Java 9+ ObjectInputFilter
ObjectInputFilter filter = ObjectInputFilter.Config.createFilter("java.base/*;!*");
ois.setObjectInputFilter(filter);

// Jackson: 禁用多态
objectMapper.deactivateDefaultTyping();

// XStream: 白名单
xstream.allowTypes(new Class[] { SafeClass.class });
```

---

## 2. Fastjson

### Version Risk Matrix

| Version Range | Risk | Notes |
|--------------|------|-------|
| < 1.2.25 | Critical | Unrestricted @type RCE |
| 1.2.25-1.2.47 | Critical | Multiple AutoType bypasses |
| 1.2.48-1.2.67 | High | Specific gadgets |
| 1.2.68-1.2.82 | Medium | expectClass bypass |
| >= 1.2.83 / 2.x | Safe* | Requires safeMode enabled |

### Bypass Techniques (Version details Claude may not fully recall)

| Version | Bypass Method |
|---------|---------------|
| 1.2.25-1.2.41 | L prefix: `Lcom.sun.rowset.JdbcRowSetImpl;` |
| 1.2.42 | Double L bypass: `LLcom.sun...;;` |
| 1.2.43-1.2.47 | Cache bypass + hash collision |
| 1.2.68+ | `AutoCloseable` expectClass bypass |

### Detection Regex

```regex
fastjson.*<version>|fastjson.*1\.2\.[0-7]
JSON\.parse|JSON\.parseObject|@type
ParserConfig.*setAutoTypeSupport|setSafeMode
```

---

## 3. JNDI Injection

### JDK Version Restrictions (Critical Boundary Information)

| JDK Version | RMI Reference | LDAP Reference | Local Gadget |
|-------------|--------------|----------------|--------------|
| < 6u141, 7u131 | Available | Available | Available |
| 6u141 ~ 8u190 | Blocked | Available | Available |
| 8u191, 11.0.1+ | Blocked | Blocked | Available |

High-version bypass: Local classpath gadgets (e.g., Tomcat BeanFactory + ELProcessor)

### Detection Regex

```regex
# JNDI calls
\.lookup\s*\(|InitialContext|JdbcRowSetImpl|\$\{jndi:
DirContext\.search|JMXConnectorFactory

# JDBC protocol injection (high-version bypass)
iiop://|iiopname:|corbaname:|corbaloc:

# Data source configuration security
DatasourceType|datasource.*config|illegalParameters
```

### JDBC Protocol Injection (Edge Case)

Some framework JDBC URL blocklists may miss IIOP protocols:
- `iiop://` / `iiopname:` / `corbaname:` / `corbaloc:`
- These protocols can trigger JNDI lookup, bypassing blocklists that only filter `rmi://` and `ldap://`

---

## 4. XXE

### Complete List of Dangerous Parsers

| Parser | Package | Default Safe? |
|--------|---------|---------------|
| DocumentBuilder | javax.xml.parsers | No |
| SAXParser | javax.xml.parsers | No |
| SAXReader | org.dom4j.io | No |
| SAXBuilder | org.jdom2.input | No |
| XMLReader | org.xml.sax | No |
| XMLInputFactory | javax.xml.stream | No |
| TransformerFactory | javax.xml.transform | No |
| Validator | javax.xml.validation | No |
| Unmarshaller | javax.xml.bind | No |
| Digester | org.apache.commons.digester | No |
| DomHelper | Various framework custom implementations (**often overlooked**) | No |

### Critical Audit Warning

- Setting only `FEATURE_SECURE_PROCESSING` is **not enough** — you must explicitly set `disallow-doctype-decl=true`
- Must search plugins/extensions directories, not just core modules
- Search for wrapper classes like DomHelper/XmlHelper/XmlUtil

### Detection Regex

```regex
# Parsers
DocumentBuilderFactory|SAXParserFactory|XMLInputFactory|TransformerFactory
SAXReader|SAXBuilder|XMLReader|Digester|DomHelper|XmlHelper

# Defense validation (must be present)
disallow-doctype-decl|FEATURE_DISALLOW_DOCTYPE
external-general-entities|external-parameter-entities

# Insufficient defense (this alone is not enough)
FEATURE_SECURE_PROCESSING
```

---

## 5. Script Engines & Expression Languages

### Dangerous Engines

| Engine | Dangerous API | CVE |
|--------|--------------|-----|
| Commons Text | `StringSubstitutor.createInterpolator().replace()` | CVE-2022-42889 |
| SnakeYAML | `new Yaml().load()` (default Constructor) | Multiple CVEs |
| Groovy | `GroovyShell.evaluate()`, `GroovyScriptEngine` | - |
| Nashorn/Rhino | `ScriptEngine.eval()` | - |
| OGNL | `OgnlUtil.getValue()` (Struts2) | Multiple CVEs |
| SpEL | `SpelExpressionParser.parseExpression().getValue()` | - |
| MVEL | `MVEL.eval()` | - |

### Detection Regex

```regex
# Commons Text (Text4Shell)
StringSubstitutor|createInterpolator

# SnakeYAML
new Yaml\(\)|Yaml\.load\(|new Constructor\(

# Groovy
GroovyShell|GroovyScriptEngine|GroovyClassLoader

# JSR-223 generic script engines
ScriptEngineManager|ScriptEngine|\.eval\s*\(
getEngineByName|getEngineByExtension

# OGNL
OgnlUtil|Ognl\.getValue|ActionContext

# SpEL
SpelExpressionParser|parseExpression|EvaluationContext
StandardEvaluationContext  # More dangerous than SimpleEvaluationContext
```

---

## 6. SQL Injection Practical Patterns

### ORM/Query Builder Dangerous Patterns

| Framework | Dangerous Pattern | Detection Regex |
|-----------|------------------|-----------------|
| MyBatis | `${}` in XML | `\$\{` (in .xml files) |
| MyBatis-Plus | `.apply()` / `.last()` | `\.apply\s*\(\|\.last\s*\(` |
| JPA/Hibernate | `createQuery()` + concatenation | `createQuery\s*\(.*\+` |
| Spring Data | `@Query(nativeQuery=true)` + concatenation | `@Query.*nativeQuery.*true` |
| jOOQ | `DSL.sql()` + concatenation | `DSL\.sql\(.*\+` |
| JDBI | `@SqlQuery` string methods | `@SqlQuery\|@SqlUpdate` |

### MyBatis `${}` Security Audit Key Points

- ORDER BY / GROUP BY clauses cannot use `#{}` parameterization — field names must be validated via allowlist
- `@DataScope` annotation + AOP aspect SQL concatenation is a hidden injection point
- Trace chain: Controller → Service → @DataScope → Aspect → Mapper.xml `${params.dataScope}`

---

## 7. Reflection Call Security

### High-Risk Patterns

| Pattern | Risk | Detection |
|---------|------|-----------|
| `method.invoke(target, params)` (user-controllable) | RCE | `method\.invoke\|Method\.invoke` |
| `getDeclaredMethod(methodName)` (user-controllable) | Arbitrary method call | `getDeclaredMethod\|getMethod` |
| `SpringContextUtil.getBean(beanName)` (user-controllable) | Bean invocation | `getBean.*String` |
| `Class.forName(className)` (user-controllable) | Class loading | `Class\.forName` |
| Scheduled task reflection execution (e.g., Ruoyi ScheduleRunnable) | RCE | `ScheduleRunnable\|QuartzJob` |

---

## 8. Audit Checklist (Advanced)

```
Deserialization:
- [ ] Search all readObject / fromXML / JSON.parse / Yaml.load
- [ ] Check Fastjson version and safeMode configuration
- [ ] Check Jackson enableDefaultTyping
- [ ] Check XStream allowlist
- [ ] Verify ObjectInputFilter configuration (Java 9+)

JNDI:
- [ ] Search InitialContext.lookup parameter sources
- [ ] Check JDK version to determine exploitable vectors
- [ ] Check JDBC URL protocol blocklist completeness (iiop/corbaname)

XXE:
- [ ] Search all XML parsers (including plugins/extensions)
- [ ] Verify disallow-doctype-decl=true (not just FEATURE_SECURE_PROCESSING)
- [ ] Search for wrapper classes like DomHelper/XmlHelper

Script Engines:
- [ ] Check commons-text version (Text4Shell)
- [ ] Search for SnakeYAML new Yaml() without SafeConstructor
- [ ] Search for ScriptEngine.eval / GroovyShell.evaluate
- [ ] Search for SpEL StandardEvaluationContext + user input

SQL Injection:
- [ ] MyBatis ${}: trace @DataScope + AOP aspects
- [ ] MyBatis-Plus .apply() / .last()
- [ ] JPA createQuery/createNativeQuery + concatenation
- [ ] Controllable sort fields (@RequestParam sort/order)

Reflection:
- [ ] method.invoke parameter source tracing
- [ ] Class.forName / getBean parameters user-controllable
- [ ] Reflection execution in scheduled task configurations
```
