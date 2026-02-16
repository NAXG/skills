# Cryptography Security Audit Module

> Loaded when the project has encryption/signing/JWT/key management operations

## Audit Checklist

### Key Management
- [ ] Are there plaintext keys in source code/configuration files
- [ ] Do environment variable names have default value fallbacks in code
- [ ] Do keys have rotation mechanisms and expiration times
- [ ] Is key storage using a dedicated key management service (KMS/Vault)

### JWT
- [ ] Is the signature verified (cannot just decode without verify)
- [ ] Is the `alg` field checked (preventing `none` algorithm attacks)
- [ ] Are `exp`/`iss`/`aud` fields checked
- [ ] Is the signing algorithm strength sufficient (HS256 requires minimum 256-bit key)
- [ ] Is the token validity period reasonable (no more than 24 hours)
- [ ] Is the Refresh Token mechanism secure

### Encryption Algorithms
- [ ] Symmetric encryption: using AES-GCM/ChaCha20-Poly1305 (not DES/RC4/ECB mode)
- [ ] Is IV/Nonce randomly generated (cannot be fixed/predictable)
- [ ] RSA key length >= 2048 bits, Padding uses OAEP
- [ ] Password hashing: using bcrypt/argon2 (not MD5/SHA direct hashing)
- [ ] Data integrity: using SHA-256+ (not MD5/SHA-1)

### Random Numbers & TLS
- [ ] Do security scenarios use CSPRNG (not Math.random/random.randint)
- [ ] TLS minimum version >= 1.2, certificate verification not disabled
- [ ] Is the HSTS header set

## Grep Search Patterns

```
Grep: secret.*=.*['"]|SECRET.*=.*['"]|key.*=.*['"]
Grep: password.*=.*['"]|PASSWORD.*=.*['"]
Grep: api_key.*=.*['"]|API_KEY.*=.*['"]
Grep: private.key|PRIVATE_KEY|-----BEGIN.*PRIVATE
Grep: jwt\.decode|jwt\.verify|JWT\.decode|JWT\.require
Grep: Algorithm\.none|algorithm.*none|alg.*none
Grep: setSigningKey|SigningKey|secret_key
Grep: expiresIn|exp|expiration|TOKEN_EXPIRY
Grep: DES|3DES|RC4|Blowfish|RC2
Grep: ECB|MODE_ECB|AES/ECB
Grep: md5|MD5|sha1|SHA1|SHA-1
Grep: bcrypt|scrypt|argon2|PBKDF2
Grep: Cipher\.getInstance|createCipheriv|AES\.new
Grep: Math\.random|random\.randint|rand\(|mt_rand|math/rand
Grep: SecureRandom|crypto\.randomBytes|secrets\.|crypto/rand
Grep: TLSv1\.0|TLSv1\.1|SSLv3|SSLv2
Grep: InsecureSkipVerify|verify.*false|VERIFY_NONE
Grep: RSA|PKCS1|OAEP|keySize|key_size
```

## Cross-References

- Related domain modules: domains/authentication.md (password storage)
