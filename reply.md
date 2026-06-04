## ✅ 重构完成：从 FastMCP 迁移到 dcc-mcp-core + Skills 架构

全部 Phase 0-6 已完成，以下是变更总结：

---

### Phase 0 — Python 版本对齐
- `pyproject.toml`：`requires-python` 从 `>=3.14` 降回 `>=3.10,<3.14`
- 新增 Python 3.13 分类器支持
- 依赖切换：移除 `fastmcp`/`mcp`，替换为 `dcc-mcp-core>=0.17.47`

### Phase 1 — ShotGridServer Adapter
- **新建** `src/shotgrid_mcp_server/shotgrid_adapter.py` — `ShotGridServer(DccServerBase)` adapter
  - 走 custom studio tool / external-bridge 模式（无 GUI host，不需要 `HostExecutionBridge`）
  - 工具默认 `affinity: any`
  - 支持凭据解析（env vars + HTTP headers）
  - 提供 `create_shotgrid_server()` 工厂函数
- **更新** `server.py` — 向后兼容，`create_server()` 返回 dcc-mcp-core 兼容的 server
- **更新** `cli.py` — 使用 `create_shotgrid_server()` 启动
- **更新** `__init__.py` — 导出 `ShotGridServer`, `create_shotgrid_server`

### Phase 2 — Shared Lib
- **新建** `src/shotgrid_mcp_server/shared_lib.py`（~800 行）
  - 从 `tools/*.py` 剥离纯业务逻辑函数
  - 零 MCP 框架依赖，只依赖 `shotgun-api3` + `shotgrid-query`
  - 覆盖 CRUD、Search、Batch、Note、Media、Playlist、Low-level API、Vendor、User/Project helpers
  - 含向后兼容别名函数

### Phase 3-5 — 8 个 Skill Packages
全部技能包已创建，总计 **41 个 tool script**：

| Skill | 激活方式 | Scripts | 说明 |
|-------|---------|--------|------|
| `shotgrid-crud` | ✅ 默认 | 5 | create/read/update/delete/entity_schema |
| `shotgrid-search` | ✅ 默认 | 7 | search_entities/find_one/advanced_search/active_projects_users |
| `shotgrid-batch` | 按需 | 3 | batch create/update/delete |
| `shotgrid-media` | 按需 | 3 | thumbnail download/upload/batch |
| `shotgrid-notes` | 按需 | 3 | create/read/update notes |
| `shotgrid-playlists` | 按需 | 4 | create/find/add/remove playlist versions |
| `shotgrid-api` | 按需 | 13 | sg_find/sg_create/sg_batch/schema_* 等底层 API |
| `shotgrid-vendor` | 按需 | 3 | find vendor users/versions/playlists |

每个 skill 包含 `SKILL.md`（含元数据 frontmatter） + `tools.yaml`（JSON Schema） + `scripts/*.py`

### Phase 6 — Release Please 配置
- **替换** `bumpversion.yml` (commitizen) → `release-please.yml` (googleapis/release-please-action)
- 新建 `release-please-config.json` + `.release-please-manifest.json`
- 发布流程：push main → release-please 自动 bump + changelog → 自动 PyPI publish
- MR 测试矩阵扩展到 Python 3.10/3.11/3.12/3.13

### 兼容性保证
- 环境变量：`SHOTGRID_URL` / `SHOTGRID_SCRIPT_NAME` / `SHOTGRID_SCRIPT_KEY` **不变**
- HTTP headers：`X-ShotGrid-*` **不变**
- CLI entry：`shotgrid-mcp-server` **不变**
- Transport：stdio + HTTP **不变**
- ASGI：`shotgrid_mcp_server.asgi:app` **不变**
- 现有 `connection_pool`, `schema_cache`, `api_client`, `models`, `exceptions` **全部保留**

### 下一步
- **推送 PR** 到 `main` 分支
- MR 合并后 release-please 会自动创建 Release PR
- Release PR 合并后自动发版到 PyPI（v1.0.0）
