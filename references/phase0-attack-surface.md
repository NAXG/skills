# Phase 0 Attack Surface Mapping

> Phase 0 is a mandatory sub-step of Phase 1. Goal: build a complete attack surface inventory before entering vulnerability scanning.

## Output Contract (Mandatory)

```text
phase0_inventory:
  modules_inventory: {completed|partial}
  entrypoint_inventory: {completed|partial}
  content_type_inventory: {completed|partial}
  dependency_inventory: {completed|partial}
  phase0_checklist: {quick_passed|all_passed|partial}
```

## 0.1 Complete Module/Plugin Inventory

Use `Glob` + `Read` to enumerate and build file-to-module relationships (select by tech stack):

- Java: `**/pom.xml`, `**/build.gradle*`, `**/settings.gradle*`
- Node.js: `**/package.json`
- Go: `**/go.mod`
- Python: `**/pyproject.toml`, `**/setup.py`, `**/requirements*.txt`

Module types that must be covered:

- core main modules
- plugins/extensions sub-modules
- tests/examples/samples
- Configuration directories and security-related config files
- CI/CD and container orchestration files

## 0.2 Complete Entry Point Inventory

Use `Grep` to generate an entry point matrix (adjust patterns by language/framework):

- HTTP/REST entry points
- WebSocket/SSE entry points
- Scheduled task entry points
- MQ/async consumer entry points
- RPC/gRPC entry points
- Deserialization/config loading entry points

Minimum matrix fields:

```text
entrypoint_matrix:
  - path_or_topic: {value}
    method_or_type: {HTTP|MQ|RPC|SCHEDULED|...}
    handler: {file:line}
    auth_guard: {present|absent|unknown}
```

### Endpoint-Permission Matrix (standard/deep only)

For standard/deep modes, Phase 0 must produce an endpoint-permission matrix as a prerequisite for D3/D9 assessment:

```text
endpoint_permission_matrix:
  - endpoint: {path}
    method: {GET|POST|PUT|DELETE|...}
    handler: {file:line}
    auth_required: {yes|no|unknown}
    role_required: {admin|user|public|unknown}
    notes: {any relevant security annotation}
```

Minimum requirements:
- **standard mode**: Focus on auth-critical and data-mutating endpoints (POST/PUT/DELETE + sensitive resources); minimum 50% endpoint coverage
- **deep mode**: List **all** discovered HTTP endpoints (from entrypoint_inventory) for full coverage
- `auth_required` must be determined by checking middleware/interceptor/decorator chains, not guessed
- If auth status cannot be determined from static analysis, mark as `unknown` (not `no`)
- This matrix is the primary input for D3 (Authorization) and D9 (Business Logic) assessments

### Substance Constraints (Prevent Step-Skipping)

`entrypoint_inventory=completed` requires:
- Contains >= 1 concrete handler (`file:line` format)
- Cannot just declare "completed" with no actual content
- Main thread validation: check whether output contains handlers in `file:line` format

## 0.3 Content-Type Sensitive Entry Points (Optional)

> This inventory is optional for all modes. When completed, it enriches the attack surface map but is not required for any gate tier.

Perform dedicated enumeration for the following types (`Grep` + `Read`):

- XML (`application/xml`, `text/xml`, `consumes.*xml`)
- JSON (`application/json`, `consumes.*json`)
- Form (`application/x-www-form-urlencoded`, `multipart/form-data`)
- Custom Content-Type

Minimum output:

```text
content_type_matrix:
  xml_endpoints: {n}
  json_endpoints: {n}
  form_endpoints: {n}
  custom_content_type_endpoints: {n}
```

## 0.4 Dependency and CVE Inventory

Use dependency manifest files and build files to generate a dependency inventory, flagging high-risk components:

- Java: `pom.xml`, `build.gradle*`
- Node.js: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Python: `requirements*.txt`, `poetry.lock`
- Go: `go.mod`, `go.sum`

Minimum output:

```text
dependency_inventory:
  total_dependencies: {n}
  high_risk_components: [{name:version:reason}]
  opaque_dependencies: [{name:version:security_role}]
```

`opaque_dependencies`: Dependencies that contain security-critical logic but whose source code is not available for audit (e.g., proprietary auth libraries, closed-source WAF modules). These must be declared in the report's Audit Limitations section as "security logic not auditable."

### Substance Constraints (Prevent Step-Skipping)

`dependency_inventory=completed` requires:
- Lists >= 1 concrete dependency (`name:version` format)
- Cannot just declare "completed" with no actual content
- Main thread validation: check whether output contains dependencies in `name:version` format

## Completion Gate

### Gate Levels

```text
quick_passed: entrypoint_inventory=completed + dependency_inventory=completed
all_passed: modules_inventory=completed + entrypoint_inventory=completed + dependency_inventory=completed
```

- `quick_passed`: used only in quick mode, proceed to Phase 2 once met
- `all_passed`: used in standard/deep modes, three core items (modules + entrypoint + dependency) must be met before proceeding to Phase 2

### Completion Criteria

Three core items met (modules + entrypoint + dependency) → `phase0_checklist: all_passed`
Only entrypoint + dependency met → `phase0_checklist: quick_passed`
Otherwise → `phase0_checklist: partial`

If partial:
- Must not proceed to Phase 2 (but can retry, see below)
- Clearly state the gap reason in RECON

### Phase 0 Retry Limit

Phase 0 allows a maximum of 2 retries (3 total attempts). Each retry **must** include:
- **Failure reason**: What specifically failed in the previous attempt
- **Improvement strategy**: Concrete changes (e.g., different Grep patterns, broader file scope, alternative glob patterns)
- **Targeted items**: Which specific inventory items will be completed
- Blind re-execution without documented improvement is prohibited

If still partial:
- Record the gap reason
- Downgrade to `phase0_checklist=partial_accepted`, allow continuation but mark the report as "incomplete reconnaissance"
- **Constraint**: `entrypoint_inventory` must be completed; otherwise downgrade is not allowed (no entry points means the audit is meaningless)

## Project Type Adaptation

### Library Projects (No HTTP Entry Points)

Detection condition: HTTP entry points = 0 in entrypoint_inventory, but exported public APIs >= 5

Handling:
- Switch entry point definition to public API functions (exported public methods/functions)
- Use `PUBLIC_API` for `method_or_type` in entrypoint_matrix
- Set D2 (Authentication), D3 (Authorization), D6 (SSRF) to N/A in the coverage matrix
- Focus on D1 (Injection), D4 (Deserialization), D5 (File Operations), D7 (Cryptography)

### Minimal Projects (<500 LOC)

- Force quick mode
- Phase 0 simplified to file list + dependency list only
- modules_inventory and content_type_inventory automatically marked as completed

### Multi-Language Projects

- When Phase 0 identifies multiple languages, annotate language proportions in RECON output
- Plan Agent splitting strategy along language boundaries
- Each language's corresponding Agent loads its own language module
