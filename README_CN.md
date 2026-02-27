# code-audit

白盒代码安全审计 Skill，通过 Source-to-Sink 数据流追踪发现真实漏洞——而非仅靠模式匹配。

设计思路来自 [3stoneBrother/code-audit](https://github.com/3stoneBrother/code-audit)。原项目文档过重，包含大量大模型已有的知识。本项目走轻量化路线——只保留结构化指令、执行控制和领域专项模式。

## 快速开始

```bash
# 安装
claude skill add gh:NAXG/skills --skill code-audit

# 使用
/code-audit standard      # 完整 OWASP 审计
/code-audit deep          # 关键系统，多轮迭代
```

### 示例

```
User: /code-audit deep

Claude: [MODE] deep
        [RECON] 326 files, Django 4.2 + DRF + PostgreSQL + Celery
        [PLAN] 4 Agents, D1-D10 coverage, estimated 90 turns
        ... (用户确认) ...
        [REPORT] 3 Critical, 7 High, 5 Medium, 2 Low
```

## 系统要求

- **Python 3**（必需）
- **semgrep**（必需）

## 覆盖范围

### 9 种语言，13 个框架

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

### 10 个安全维度

| # | 维度 | 审计轨道 | 发现什么 |
|---|------|---------|---------|
| D1 | 注入 | Sink 驱动 | SQLi, CMDi, LDAP, SSTI, SpEL, XSS, NoSQL |
| D2 | 认证 | 配置驱动 | Token/Session 缺陷、弱密码、绕过 |
| D3 | 授权 | 控制驱动 | IDOR、越权、缺失访问控制 |
| D4 | 反序列化 | Sink 驱动 | Java/Python/PHP gadget 链、XXE |
| D5 | 文件操作 | Sink 驱动 | 上传、路径穿越、Zip Slip |
| D6 | SSRF | Sink 驱动 | URL 注入、DNS 重绑定 |
| D7 | 密码学 | 配置驱动 | 硬编码密钥、弱算法、IV 复用 |
| D8 | 配置安全 | 配置驱动 | 调试接口暴露、CORS、错误信息泄露 |
| D9 | 业务逻辑 | 控制驱动 | 竞态条件、流程绕过、批量赋值 |
| D10 | 供应链 | 配置驱动 | 依赖 CVE、过时组件 |

### 12 个安全域模块

SQL 注入、命令注入、XSS、认证、授权、文件操作、SSRF、反序列化、API 安全、LLM/AI 安全、竞态条件、密码学。

## 架构

### 审计模式

| 模式 | 轮次 | 阶段 | Agent 数量 |
|------|------|------|-----------|
| `standard` | 1–2 | 侦察 → 扫描 → 合并 → 深挖 → 验证 → 报告 | 按规模分配 |
| `deep` | 2–3 | 完整流水线，多轮迭代 + 收敛控制 | 按规模分配 |

### 多 Agent 工作流

```
Phase 1: 侦察
  ├─ 技术栈识别
  ├─ 攻击面映射
  └─ 入口点盘点

Phase 2: 扫描（并行 Agent）
  ├─ Semgrep 基线扫描 (standard/deep)
  ├─ Agent 1: 注入 (D1)                [Sink 驱动]
  ├─ Agent 2: 认证 + 授权 (D2+D3+D9)  [控制驱动]
  ├─ Agent 3: 文件 + SSRF (D5+D6)     [Sink 驱动]
  └─ Agent N: ...                      [按项目规模分配]

Phase 2.5: 合并
  ├─ 输出收集 & 格式验证
  └─ 预验证统计

Phase 3: 深挖 (standard/deep)
  ├─ 补全未完成的数据流
  └─ 跨 Agent 攻击链合成

Phase 4: 验证 (standard/deep)
  ├─ Semgrep 交叉验证
  ├─ 多 Agent 交叉验证
  └─ 严重性校准

Phase 5: 报告
  └─ 带证据和 PoC 的结构化输出
```

### Source → 传播 → Sink

每个漏洞都通过相同的模型追踪：

1. **Source** — 攻击者可控数据的入口
2. **传播** — 过滤/转换是否有效
3. **Sink** — 危险操作是否可达

### 反幻觉

- 文件路径必须通过 Glob/Read 验证后才能写入报告
- 代码片段必须来自 Read 工具的实际输出
- 禁止捏造路径、禁止猜测代码
- **核心原则：宁可漏报，不可误报**

## 报告输出

| 章节 | standard | deep |
|------|:--------:|:----:|
| 执行摘要 | ✓ | ✓ |
| 发现统计 | ✓ | ✓ |
| 覆盖矩阵 (D1–D10) | ✓ | ✓ |
| 漏洞详情 + PoC | ✓ | ✓ |
| 审计局限性 | ✓ | ✓ |
| Semgrep 验证证据 | ✓ | ✓ |
| 攻击链分析 | ✓ | ✓ |
| 攻击路径评分 | ✓ | ✓ |

## 项目结构

```
code-audit/
├── SKILL.md                     # Skill 入口
├── scripts/
│   └── parse_semgrep_baseline.py
├── references/          (12)    # 执行控制与方法论
├── languages/            (9)    # 语言专项审计模式
├── frameworks/          (13)    # 框架专项审计模式
└── domains/             (12)    # 安全域模块
```

## 许可证

MIT

## 局限性

### 知识截止日期

本 Skill 依赖大模型进行分析。当前模型的知识截止日期约为 **2025 年 6 月**。

- **供应链 (D10)** 阶段对在此日期之后发布的 CVE 覆盖可能不完整
- 建议配合外部工具使用：
  - `semgrep` — SAST 基线扫描
  - `osv-scanner` — 依赖漏洞检测

### 算力限制

大模型分析受限于上下文窗口和推理预算。对于大型代码库，覆盖可能不完整——部分文件或数据流可能被遗漏。审计结果应作为全面人工审查的补充，而非替代。

### 工具整合

本 Skill 专注于 **Source-to-Sink 数据流追踪**。外部扫描器可以补充但无法替代以下手动分析：
- 业务逻辑漏洞
- 复杂的认证/授权缺陷
- 多步骤攻击链

## 免责声明

本 Skill 仅用于**授权安全测试**。使用者必须拥有审计目标代码的合法授权，并遵守适用法律。未经授权对他人系统进行安全测试可能违法。
