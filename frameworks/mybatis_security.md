# MyBatis Security Cheat Sheet

> Version scope: MyBatis 3.x, MyBatis-Plus | Load condition: mybatis configuration or *Mapper.xml detected

## Security Configuration Pitfalls

| Pitfall | Risk | Detection Signal |
|---------|------|------------------|
| `${}` in WHERE/AND/OR | SQL injection (Critical) | `WHERE name = '${name}'` |
| `${}` in ORDER BY | Blind injection (High) | `ORDER BY ${sortColumn}` |
| `${}` in LIKE | SQL injection | `LIKE '%${name}%'` |
| `${}` in table/column names | SQL injection (Critical) | `FROM ${tableName}` |
| `${}` in `<if>/<when>` | Hidden injection | Injection only triggered when condition is met |
| `${}` in `<foreach>` | SQL injection | Concatenation inside loop body |
| MyBatis-Plus apply() concatenation | SQL injection | `.apply("..." + var)` |
| MyBatis-Plus last() concatenation | SQL injection | `.last("LIMIT " + var)` |
| @SelectProvider string concatenation | SQL injection | `"SELECT..." + var` in Provider class |
| Java-layer StringBuilder building SQL | Indirect injection | Concatenated then passed into `${condition}` |

Core: `#{}` = PreparedStatement parameter binding (safe), `${}` = direct string substitution (dangerous)

## Sink Mapping

| Framework API | Sink Type | Notes |
|---------------|-----------|-------|
| XML `${param}` | SQL injection | Direct string substitution |
| `wrapper.apply("..." + var)` | SQL injection | MyBatis-Plus SQL fragment concatenation |
| `wrapper.last("..." + var)` | SQL injection | Appends arbitrary SQL |
| `wrapper.having("..." + var)` | SQL injection | HAVING concatenation |
| `wrapper.exists("..." + var)` | SQL injection | Subquery concatenation |
| `wrapper.orderByAsc(userInput)` | SQL injection | User-controllable sort field |
| `@SelectProvider` / `@UpdateProvider` | SQL injection | Provider method concatenation |

## Grep Search Patterns

```
# XML ${} full scan
\$\{[^}]+\}

# WHERE condition injection (Critical)
(WHERE|AND|OR|HAVING|SET)\s.*\$\{

# ORDER/LIMIT injection (High)
(ORDER\s+BY|GROUP\s+BY|LIMIT|OFFSET)\s+\$\{

# Table/column name injection (High)
(FROM|INTO|UPDATE|JOIN|SELECT)\s+\$\{

# LIKE injection
LIKE\s+['"]?%?\$\{

# Hidden in conditional branches
<if\s+test=.*\$\{|<when\s+test=.*\$\{|<foreach.*\$\{

# MyBatis-Plus
\.apply\s*\(.*\+|\.last\s*\(.*\+|\.having\s*\(.*\+|\.exists\s*\(.*\+

# Provider
@(Select|Insert|Update|Delete)Provider

# Java-layer concatenation
String\.format\s*\(.*"(SELECT|WHERE|ORDER|INSERT|UPDATE|DELETE)
"(SELECT|WHERE|ORDER|INSERT|UPDATE|DELETE).*"\s*\+
StringBuilder.*append.*"(SELECT|WHERE|ORDER)"
```

## Audit Checklist

- [ ] Full scan of all `${}` usage in XML
- [ ] Categorize `${}`: WHERE / ORDER BY / table-column names / LIKE / LIMIT
- [ ] Hidden `${}` inside `<if>/<when>/<foreach>`
- [ ] Trace each `${}` parameter data source (Controller -> Service -> Mapper)
- [ ] MyBatis-Plus apply()/last()/having()/exists() concatenation
- [ ] @SelectProvider/@UpdateProvider string concatenation
- [ ] Java-layer StringBuilder/String.format building SQL fragments
- [ ] Second-order injection: values from database re-concatenated into SQL
- [ ] ORDER BY / table-column name whitelist validation
- [ ] Whether LIKE uses `CONCAT('%', #{}, '%')` pattern
