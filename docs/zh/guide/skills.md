# Skills

本服务器实现了 MCP **Skills** 扩展（`io.modelcontextprotocol/skills`，SEP-2640）。
Skills 即 [Agent Skills](https://agentskills.io/specification)：一个包含 `SKILL.md`
与可选支撑文件的目录，通过 MCP 暴露出来，让描述本服务器用法的工作流指令随服务器一起分发。

所有能力都建立在标准的 Resources 原语之上：`skills/list` 发现技能，
`skills/get` 按 URI 解析，`resources/read` 读取内容。

## 内置技能

`src/shotgrid_mcp_server/data/skills` 下内置了三个技能：

| 技能 | 覆盖范围 |
|------|----------|
| `shotgrid-entity-search` | 选择合适的搜索工具、编写正确的过滤条件 |
| `shotgrid-task-management` | 读取、更新与批量处理任务，避免误改字段 |
| `shotgrid-schema-discovery` | 写入前确认实体类型、字段名与状态码 |

每个技能都额外带一个 `references/` 下的支撑文件，便于验证多文件清单机制。

## 添加自己的技能

把 `SHOTGRID_MCP_SKILLS_DIR` 指向一个或多个目录（Windows 用 `;` 分隔，
其它系统用 `:` 分隔）。每个含 `SKILL.md` 的直接子目录即成为一个技能：

```text
skills/
└── studio-publish-workflow/
    ├── SKILL.md
    └── references/
        └── naming.md
```

```bash
# Windows
set SHOTGRID_MCP_SKILLS_DIR=C:\studio\skills;D:\shared\skills
# macOS / Linux
export SHOTGRID_MCP_SKILLS_DIR=/studio/skills:/shared/skills
```

每个 `SKILL.md` 必须以 YAML frontmatter 开头并包含 `name` 与 `description`，
且 `name` 必须等于目录名。不满足规则的目录会被跳过并记录一条日志，
而不是半残地对外提供服务；如果技能没有出现，请查看服务器日志。

内置技能优先扫描。用户目录中的同名技能不会覆盖内置技能。

## 限制

SEP-2640 要求单个技能不超过 **512 个文件**、**16 MiB**。超出限制的技能仍会
被服务，但服务器会打印警告——因为符合规范的 host 不再保证能加载它。

## 一致性校验

清单基于服务器实际下发的字节计算，因此 host 可以按 `size` 与 SHA-256 `digest`
校验读到的每个文件，并逐字段比对 `SKILL.md` 的 frontmatter。文本文件按字节
原样下发：以 CRLF 编写的技能，下发时仍是 CRLF。

复现端到端证据：

```bash
uv run python scripts/verify_skills_extension.py
```

该脚本会以 HTTP 传输启动真实服务器，用裸 JSON-RPC 驱动它，打印
`server/discover`、`skills/list`、`skills/get` 与 `resources/read` 的响应，
并列出违反规范的条目（全部通过时为空）。

每个 pull request 的 CI 都会执行它（`vx just verify-skills`）。它是唯一能看到
序列化字段名的检查：单元测试读的是 Python 属性，因此即使 camelCase 线上字段名
（`ttlMs`、`cacheScope`）不再出现，单测依然全绿。

## Host 支持情况

**服务端实现已完整且符合规范。** MCP Skills 的 host 侧支持仍在各 MCP 客户端
中推进；未实现该扩展的 host 不会调用 `skills/list` 与 `skills/get`，行为不变。
扩展在 `server/discover` 路径上宣告：

```json
{
  "capabilities": {
    "resources": { "subscribe": false, "listChanged": false },
    "extensions": {
      "io.modelcontextprotocol/skills": { "directoryRead": false }
    }
  }
}
```

旧版 `initialize` 握手早于扩展机制，不携带 `capabilities.extensions` 字段；
那里缺失该字段是预期行为，不是缺陷。

`directoryRead` 为 `false`：本服务器不实现 `resources/directory/read`。
技能的每个文件都会出现在 `resources/list` 中且可单独寻址，host 依据清单即可
浏览技能，无需目录读取。
