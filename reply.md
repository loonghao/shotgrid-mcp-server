已完成第二轮重构修正，commit `2c15f5a` 已推送到 PR #149。

### 本次修正内容

**1. Adapter 彻底重写**
- 移除 `server._server` 私有属性访问（违反 dcc-mcp-creator 原则）
- 使用 `DccServerBase.start()` 公共 API 启动服务
- 通过 `enable_gateway_failover=True` 自动注册到 dcc-gateway（127.0.0.1:9765）

**2. 所有 41 个脚本重写**
- 使用 `dcc_mcp_core.skill` 的 `@skill_entry` 装饰器
- 使用 `skill_success()` 包装返回值
- 使用 `run_main()` 替代手写 argparse/sys.exit
- 符合 skill authoring checklist 规范

**3. 所有 8 个 tools.yaml 增强**
- 添加 `source_file`, `execution: sync`, `affinity: any`
- 添加 `read_only`, `idempotent`, `destructive` 安全标注
- 写入工具添加 `next_tools.on_failure: dcc_diagnostics__error_report`

**4. SKILL.md metadata 规范化**
- `layer`: data/domain（而非非标准 "default"）
- `stage`: discovery/mutate/pipeline
- description 格式：`<Layer> skill — <scope>. Use when <trigger>. Not for <counter-example>.`

**5. 新增 8 个 groups.yaml**
- 每个 skill 有 `default` (all tools) 和 `read-only` 分组

**6. 删除 reply.md 临时文件**

**7. Gateway 验证**
```
✓ dcc_name=shotgrid
✓ Gateway port: 9765 (v0.17.53, healthy)
✓ Registered in FileRegistry
```

### 启动方式
```bash
uvx shotgrid-mcp-server
# → HTTP server on 8765, registered with gateway at http://127.0.0.1:9765/mcp
```
