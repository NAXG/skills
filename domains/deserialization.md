# Deserialization Security Audit Module

> Scope: All projects using object serialization/deserialization
> Related dimensions: D1 (Injection Vulnerabilities), D5 (System Interaction Security)
> Loaded when deserialization sinks are detected

## Audit Checklist

- [ ] Are there deserialization operations on untrusted data
- [ ] Can JSON be used instead of binary serialization formats
- [ ] Java: Is ObjectInputFilter used to restrict allowed classes
- [ ] Python: Is `yaml.safe_load()` used instead of `yaml.load()`
- [ ] Python: Does `pickle.loads()` process untrusted data
- [ ] PHP: Does `unserialize()` use `allowed_classes` restriction
- [ ] Ruby: Is `YAML.safe_load()` used instead of `YAML.load()`
- [ ] Is the polymorphic type configuration for Jackson/Fastjson/XStream secure
- [ ] Are there known gadget libraries in the classpath
- [ ] Do RMI/JMX/message queue communications use deserialization

## Framework/Library-Specific Pitfalls

- **Jackson**: `enableDefaultTyping()` or `@JsonTypeInfo(use=Id.CLASS)` allows arbitrary class instantiation
- **Fastjson**: When `autoType` is enabled, arbitrary classes can be instantiated; has historically bypassed blacklists multiple times
- **XStream**: No security restrictions by default; security framework configuration required
- **Python pickle**: `__reduce__` method can directly execute arbitrary code without a gadget chain
- **PHP unserialize**: POP chain exploits `__wakeup`/`__destruct`/`__toString` magic methods
- **Ruby Marshal**: `Marshal.load` can execute arbitrary code; YAML.load is unsafe by default in Ruby < 3.1
- **Java gadget libraries**: Commons Collections 3.x/4.x, Commons BeanUtils, Spring, and Hibernate all have known chains

## Grep Search Patterns

```
Grep: ObjectInputStream|readObject\(\)|readUnshared\(\)
Grep: XMLDecoder|XStream|fromXML
Grep: pickle\.loads|pickle\.load|cPickle|shelve\.open
Grep: yaml\.load\((?!.*safe)|yaml\.unsafe_load|Loader=yaml\.FullLoader
Grep: unserialize\(|__wakeup|__destruct|__toString
Grep: Marshal\.load|Marshal\.restore|YAML\.load
Grep: enableDefaultTyping|@JsonTypeInfo|autoType|AutoType
Grep: Fastjson|JSON\.parse.*Feature|parseObject
Grep: SerializationUtils\.deserialize|readObjectData
Grep: RMI|rmiregistry|JMXConnector
```

## Cross-References

- Related domain modules: domains/api-security.md (API request body deserialization), domains/cryptography.md (signature verification of serialized data)
- Related language modules: languages/java.md, languages/python.md
