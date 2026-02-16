# Authentication Security Audit Module

> Scope: All projects with user authentication functionality
> Related dimensions: D2 (Authentication & Session Management), D6 (Credential Storage Security)
> Loaded when login/registration/password-related functionality is detected

## Audit Checklist

- [ ] Is password storage using bcrypt/argon2/scrypt (not MD5/SHA)
- [ ] Is the password policy reasonable (minimum length, complexity, not in common password lists)
- [ ] Is the session ID regenerated after login (session fixation prevention)
- [ ] Does the login endpoint have rate limiting
- [ ] Are login error messages uniform (not revealing whether user exists)
- [ ] Are Session Cookies set with HttpOnly + Secure + SameSite
- [ ] Do sessions have absolute and idle timeouts
- [ ] Is the "remember me" token securely generated and revocable
- [ ] Does the password reset token have an expiration time and single-use enforcement
- [ ] Is MFA enforced server-side (cannot skip MFA step to directly access protected resources)
- [ ] Does logout properly destroy the server-side session

## Framework-Specific Pitfalls

- **Flask**: `session.regenerate()` must be called manually; session is not regenerated after login by default
- **Spring Security**: `sessionManagement().sessionFixation()` requires explicit configuration
- **Django**: `login()` automatically rotates session, but custom authentication flows may miss this
- **Express/Passport**: `req.session.regenerate()` must be called manually

## Grep Search Patterns

```
Grep: md5|MD5|sha1|SHA1|sha256|SHA-256
Grep: bcrypt|argon2|scrypt|PBKDF2|pbkdf2
Grep: hashlib\.|MessageDigest|createHash
Grep: login|authenticate|sign_in|signIn
Grep: session.*regenerate|invalidate.*session|session\.clear
Grep: rate.limit|throttle|RateLimit|LoginAttempt
Grep: password.*reset|reset.*password|forgot.*password
Grep: remember.*token|remember_me|persistent.*session
Grep: mfa|totp|two.factor|2fa|otp
Grep: HttpOnly|Secure|SameSite|cookie.*flag
```

## Cross-References

- Related domain modules: domains/authorization.md (authorization checks), domains/cryptography.md (password hashing & JWT), domains/api-security.md (API authentication)
