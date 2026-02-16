# code-audit

**版本**: 5.2.0

一套结构化、多阶段的安全审计系统，通过 Source-to-Sink 数据流追踪发现真实漏洞——而非仅靠模式匹配。覆盖 OWASP Top 10、认证/授权链、注入缺陷、反序列化、SSRF 等。

设计思路来自 [3stoneBrother/code-audit](https://github.com/3stoneBrother/code-audit)。原项目文档过重，包含大量大模型已有的知识。本项目走轻量化路线——剥离冗余内容，只保留真正能引导审计 Agent 产出更好结果的结构化指令、执行控制和领域专项模式。

## 特性

- **10 维度覆盖** — 系统化审计注入、认证、授权、反序列化、文件操作、SSRF、密码学、配置安全、业务逻辑和供应链
- **Source-to-Sink 追踪** — 从入口点追踪用户输入，经过变换到达危险操作，消除误报
- **多 Agent 架构** — 按语言、框架或安全域划分，并行扫描
- **三种审计模式** — `quick` 用于 CI/CD，`standard` 用于常规审计，`deep` 用于关键系统的多轮迭代审计
- **反幻觉规则** — 报告的每个漏洞都必须引用工具实际读取的代码；禁止猜测路径或捏造代码片段
- **Semgrep 集成** — 可选的基线扫描，支持自动结果解析和交叉验证
- **结构化报告** — 发现包含 CVSS 评分、数据流图、PoC 载荷、攻击链分析和攻击路径评分

## 支持的语言和框架

| 语言 | 框架 |
|------|------|
| Java | Spring, MyBatis |
| Python | Django, Flask, FastAPI |
| Go | Gin |
| JavaScript/TypeScript | Express, Koa, NestJS/Fastify |
| PHP | Laravel |
| Ruby | Rails |
| C# / .NET | ASP.NET Core |
| C/C++ | — |
| Rust | Actix-web, Axum, Rocket |

## 安全域

内置专项分析模块：SQL 注入、命令注入、XSS、认证、授权、文件操作、SSRF、反序列化、API 安全、LLM/AI 安全、竞态条件和密码学。

## 安装

```bash
claude install gh:anthropics/claude-code-skill-code-audit
```

或手动将本仓库克隆到 Claude Code 的 skills 目录中。

## 系统要求

- **Python 3**（必需）
- **semgrep**（推荐——增强基线扫描能力，但没有它审计也能正常进行）

## 使用方法

在 Claude Code 中调用：

```
/code-audit quick      # 快速扫描 — 适用于 CI/CD、小型项目
/code-audit standard   # 完整 OWASP 审计，含验证环节
/code-audit deep       # 多轮审计，适用于关键系统
```

### 审计模式

| 模式 | 适用场景 | 轮次 | 阶段 | Agent 数量 |
|------|---------|------|------|-----------|
| `quick` | CI/CD、小型项目 | 1 | 侦察 → 扫描 → 报告 | 1–3 |
| `standard` | 常规审计 | 1–2 | 侦察 → 扫描 → 合并 → 深挖 → 验证 → 报告 | 按规模分配 |
| `deep` | 关键系统 | 2–3 | 完整流水线，多轮迭代 + 攻击链 | 按规模分配 |

### 审计阶段

1. **Phase 1 — 侦察**：攻击面映射、技术栈识别、入口点盘点
2. **Phase 2 — 扫描**：并行 Agent 扫描全部 10 个维度
3. **Phase 2.5 — 合并**：Agent 输出收集、去重、预验证统计
4. **Phase 3 — 深挖**：跨 Agent 攻击链合成、更深层数据流分析
5. **Phase 4 — 验证**：Semgrep 交叉验证、多 Agent 交叉验证、严重性校准
6. **Phase 5 — 报告**：带证据和 PoC 的结构化安全报告

## 报告输出

报告包含：

- **执行摘要** — 项目范围、技术栈、覆盖率统计
- **发现统计** — 严重性分布（Critical / High / Medium / Low）
- **覆盖矩阵** — D1–D10 维度状态
- **漏洞详情** — 文件位置、数据流、证据、PoC、影响
- **攻击链分析** — 多步骤利用路径（standard/deep）
- **攻击路径评分** — 认证要求、复杂度、成功率（standard/deep）
- **审计局限性** — 未覆盖区域、N/A 说明、静态分析约束

## 工作原理

审计遵循攻击者思维：*每行代码在被证明安全之前，都视为可利用的*。

所有漏洞通过 **Source → 传播 → Sink** 模型评估：

1. **找到 Source** — 识别攻击面（用户输入、外部数据）
2. **追踪传播** — 检查过滤/转换是否有效
3. **检查 Sink** — 判断危险操作是否可达

优先级计算公式：

```
优先级 = (攻击面大小 × 潜在影响) / 利用复杂度
```

## 项目结构

```
code-audit/
├── SKILL.md                    # Skill 定义与入口
├── scripts/
│   └── parse_semgrep_baseline.py
├── references/                 # 执行控制与方法论
│   ├── execution-controller.md   # 执行控制器
│   ├── agent-contract.md         # Agent 契约
│   ├── coverage-matrix.md        # 覆盖矩阵
│   ├── validation-and-severity.md # 验证与严重性
│   ├── report-template.md        # 报告模板
│   ├── data-flow-methodology.md  # 数据流方法论
│   ├── phase0-attack-surface.md  # 攻击面映射
│   ├── pattern-library-routing.md # 模式库路由
│   ├── semgrep-playbook.md       # Semgrep 执行手册
│   └── agent-output-recovery.md  # Agent 输出恢复
├── languages/                  # 语言专项审计模式
│   ├── java.md, java-advanced.md
│   ├── python.md, javascript.md
│   ├── go.md, php.md, ruby.md
│   ├── c_cpp.md, rust.md
│   └── dotnet.md
├── frameworks/                 # 框架专项审计模式
│   ├── spring.md, django.md, flask.md
│   ├── fastapi.md, express.md, koa.md
│   ├── gin.md, laravel.md, rails.md
│   ├── nest_fastify.md, dotnet.md
│   ├── rust_web.md
│   └── mybatis_security.md
└── domains/                    # 安全域模块
    ├── sql-injection.md, xss.md
    ├── command-injection.md
    ├── authentication.md, authorization.md
    ├── file-operations.md, ssrf.md
    ├── deserialization.md
    ├── api-security.md, cryptography.md
    ├── race-conditions.md
    └── llm-security.md
```

## 许可证

MIT
