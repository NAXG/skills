# Authorization Security Audit Module

> Scope: All projects with role/permission/access control functionality
> Related dimensions: D2 (Authentication & Authorization), D3 (Data Access Control)
> Loaded when role/permission/access control related functionality is detected

## Audit Checklist

- [ ] Are all sensitive operations verified for permissions on the server side
- [ ] Does resource access verify ownership / IDOR protection (cannot query by ID alone, must filter by current user)
- [ ] Do API endpoints have unified permission middleware
- [ ] Is the default policy deny by default
- [ ] Do permission checks cover all CRUD operations (not just reads)
- [ ] Do bulk operation endpoints verify permissions for each item
- [ ] Do admin functions have separate authentication and authorization checks (cannot rely on URL obscurity alone)
- [ ] Do permission changes have audit logging
- [ ] Does role assignment follow the principle of least privilege
- [ ] Is there a "super admin" role that bypasses all checks

## Framework-Specific Pitfalls

- **Django**: `@login_required` only verifies login, not roles; must combine with `@permission_required` or django-guardian for object-level permissions
- **Spring Security**: `anyRequest().permitAll()` should be changed to `.authenticated()`; `@PreAuthorize` must be explicitly declared on each method
- **Rails**: `Model.find(params[:id])` queries globally without ownership filtering; use `current_user.models.find()` or Pundit/CanCanCan
- **Flask**: Blueprints lack global permission checks; must handle uniformly in `before_request` or decorators

## Grep Search Patterns

```
Grep: @login_required|@authenticated|isAuthenticated
Grep: @admin_required|hasRole|@PreAuthorize|@Secured|@RolesAllowed
Grep: authorize|Pundit|CanCan|cancan|ability
Grep: permission|Permission|PERMISSION
Grep: \.get\(.*id\)|\.find\(.*params\[:id\]|findById
Grep: current_user|request\.user|@AuthenticationPrincipal
Grep: anyRequest\(\)|permitAll|denyAll
Grep: role|Role|ROLE_|is_admin|is_staff|is_superuser
```

## Cross-References

- Related domain modules: domains/authentication.md (authentication basics), domains/api-security.md (API permissions)
