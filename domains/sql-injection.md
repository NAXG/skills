# SQL Injection Security Audit Module

> Scope: All projects using relational databases
> Related dimensions: D1 (Injection Vulnerabilities), D3 (Data Access Layer Security)
> Loaded when database dependencies or SQL-related sinks are detected

## Audit Checklist

- [ ] Do all SQL statements use parameterized queries/prepared statements
- [ ] Do ORM raw/extra/literal methods receive user input
- [ ] Are there `${}` placeholders in MyBatis mapping files
- [ ] Do non-parameterizable parts like ORDER BY / LIMIT / table names / column names use whitelist validation
- [ ] Do stored procedures contain dynamic SQL concatenation (`EXEC`/`sp_executesql`)
- [ ] Does the database connection use a least-privilege account
- [ ] Do error pages leak SQL syntax details
- [ ] Is there a second-order injection risk (database data reused for SQL construction)

## Framework/ORM-Specific Pitfalls

- **MyBatis**: `${}` concatenates directly, `#{}` is parameterized; ORDER BY is often forced to use `${}`
- **Django**: `extra()` and `raw()` accept raw SQL, bypassing ORM safety layer
- **ActiveRecord**: `where("col = '#{var}'")` string interpolation is unsafe; use `where(col: var)` or `where("col = ?", var)`
- **SQLAlchemy**: `text()` concatenation is unsafe; use `:param` named parameters
- **Sequelize**: `sequelize.query()` replacements must be explicitly used
- **JDBC**: `PreparedStatement` is ineffective if SQL is concatenated before being passed in

## Grep Search Patterns

```
Grep: execute\(.*["\'].*SELECT|execute\(.*["\'].*INSERT|execute\(.*["\'].*UPDATE|execute\(.*["\'].*DELETE
Grep: \+\s*['"].*WHERE|%s.*WHERE|\.format\(.*WHERE|\$\{.*\}
Grep: \.raw\(|\.extra\(|\.rawQuery\(
Grep: Statement\.execute|createStatement\(\)
Grep: fmt\.Sprintf.*SELECT|fmt\.Sprintf.*INSERT|fmt\.Sprintf.*UPDATE
Grep: ORDER BY.*\$|ORDER BY.*\+|ORDER BY.*%s
Grep: EXEC\s|sp_executesql|EXECUTE\s+IMMEDIATE
```

## Cross-References

- Related domain modules: domains/api-security.md (API input validation)
- Related language modules: languages/java.md, languages/python.md, languages/go.md
