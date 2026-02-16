# Spring Security Cheat Sheet

> Version scope: Spring Boot 2.x/3.x, Spring Security, Spring Data | Load condition: pom.xml contains spring-boot

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| Actuator exposes all endpoints | Information disclosure/RCE | `management.endpoints.web.exposure.include: "*"` |
| Actuator env shows values | Credential leakage | `show-values: ALWAYS` |
| Spring Cloud Gateway Actuator RCE | RCE (CVE-2022-22947) | `endpoint.gateway.enabled: true` |
| CSRF globally disabled | CSRF | `csrf().disable()` |
| permitAll overuse | Authentication bypass | `antMatchers("/**").permitAll()` |
| Security filter chain ordering | Authentication bypass | Broader rules placed before strict rules |
| @PreAuthorize concatenation | SpEL injection | `@PreAuthorize("hasRole('" + var + "')")` |
| Jackson enableDefaultTyping | Deserialization RCE | `enableDefaultTyping()` |
| @JsonTypeInfo(use=Id.CLASS) | Deserialization RCE | Allows arbitrary class instantiation |
| show-sql/include-stacktrace | Information disclosure | `show-sql=true`, `include-stacktrace=always` |
| Static resource file: protocol | Path traversal (CVE-2018-1271) | `addResourceLocations("file:")` |
| @DataScope annotation | SQL injection | `${params.dataScope}` concatenation in AOP |

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| `SpelExpressionParser.parseExpression()` | SpEL injection | User input enters expression |
| `@Value("#{...}")` | SpEL injection | `#{}` is SpEL, `${}` is property placeholder |
| `JdbcTemplate.query(String sql)` | SQL | First parameter can be concatenated |
| `entityManager.createQuery(String)` | HQL | String-concatenated HQL |
| `@Query(value = "..." + var)` | SQL/HQL | Concatenation in annotation |
| `RestTemplate.getForObject(url)` | SSRF | url from user input |
| `WebClient.create(url)` | SSRF | Same as above |
| `getOriginalFilename() + transferTo()` | Path traversal | Filename not sanitized |
| `DocumentBuilderFactory.newInstance()` | XXE | External entities not disabled |
| `"redirect:" + userInput` | Open redirect | Return value concatenation |
| `Jwts.parser().parse()` | JWT bypass | No setSigningKey |

## Grep Search Patterns

```
# SpEL injection
@Value\s*\(.*#\{.*\}.*\)|SpelExpressionParser|parseExpression\s*\(
StandardEvaluationContext

# SQL/HQL injection
@Query.*\+\s*[a-zA-Z]|createQuery\s*\(.*\+|jdbcTemplate\.(query|update).*\+
String.*=.*"SELECT.*\+

# Deserialization
enableDefaultTyping|@JsonTypeInfo.*Id\.CLASS|readObject\s*\(
new\s+XStream\s*\(\)

# Actuator
management\.endpoints.*include.*\*

# Authentication & authorization
permitAll\(\)|csrf\(\)\.disable|@PreAuthorize.*\+

# XXE
DocumentBuilderFactory\.newInstance|SAXParserFactory\.newInstance

# File operations
getOriginalFilename\(\).*transferTo|FileCopyUtils

# SSRF
RestTemplate|WebClient.*getParameter|getForObject.*request

# Open redirect
return.*"redirect:".*request|ModelAndView.*"forward:"

# Sensitive information
printStackTrace|getStackTrace|show-sql=true|include-stacktrace=always

# CORS
allowedOrigins.*\*|allowCredentials.*true

# JWT
\.parse\((?!.*setSigningKey)|SECRET.*=.*"[^"]{1,16}"

# @DataScope SQL injection
@DataScope|params\.dataScope|\$\{params\.dataScope\}
```

## Audit Checklist

- [ ] Spring Boot version and known CVEs
- [ ] SpelExpressionParser usage (SpEL injection)
- [ ] Actuator endpoint exposure scope
- [ ] SQL/HQL string concatenation
- [ ] enableDefaultTyping / @JsonTypeInfo (deserialization)
- [ ] File upload path handling
- [ ] RestTemplate/WebClient SSRF
- [ ] CORS allowedOrigins configuration
- [ ] Security filterChain ordering and permitAll scope
- [ ] Whether CSRF disabling is justified
- [ ] JWT signature verification and key strength
- [ ] Whether exception handling leaks stack traces
- [ ] XXE protection (DocumentBuilderFactory configuration)
- [ ] application.properties/yml sensitive configuration
- [ ] @DataScope / AOP aspect SQL concatenation
