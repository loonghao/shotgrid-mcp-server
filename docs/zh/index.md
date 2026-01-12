---
layout: home

hero:
  name: "ShotGrid MCP Server"
  text: "AI 驱动的 ShotGrid 集成"
  tagline: 一个用于 Autodesk ShotGrid/Flow Production Tracking 的 Model Context Protocol 服务器
  image:
    src: /logo.png
    alt: ShotGrid MCP Server
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/guide/getting-started
    - theme: alt
      text: GitHub
      link: https://github.com/loonghao/shotgrid-mcp-server

features:
  - icon: 🛠️
    title: 40+ 工具
    details: 完整的 CRUD 操作、批量处理、缩略图、备注和播放列表
  - icon: ⚡
    title: 高性能
    details: 连接池、Schema 缓存、延迟初始化
  - icon: 🚀
    title: 多种传输方式
    details: stdio（本地）、HTTP（远程）、ASGI（生产）
  - icon: 🐳
    title: 易于部署
    details: Docker、FastMCP Cloud、uvicorn/gunicorn、任意 ASGI 服务器
---

## 演示

### 0. 代码编辑器配置 ShotGrid MCP

![代码编辑器配置 ShotGrid MCP](/00-codebuddy-config-shotgrid-mcp.gif)

### 1. 查询任务安排与工作量可视化

![查询任务安排与工作量可视化](/01-query-projects-visualize-tasks.gif)

**提示词：** `查询近一周的组员任务安排，工作量的负载率每天按照工时8小时来算，用 web 方式可视化显示`

### 2. 批量创建资产与任务分配

![批量创建资产与任务分配](/02-batch-create-assets-tasks-assign.gif)

**提示词：** `将上述推荐的阵容的英雄在 shotgrid Demo:Animation 项目上批量创建，归类到角色里面，并使用 FilmVFX-CharacterAsset 任务模版，任务分配给杨卓，任务的起始时间结束时间范围为下周`

### 3. 统计 TimeLog 数据并可视化

![统计 TimeLog 数据并可视化](/03-timelog-statistics-visualize.gif)

**提示词：** `查询 shotgrid 上的 timelog 数据并以 web 的方式可视化显示出来`

### 4. 部门效率统计并发送企业微信

![部门效率统计并发送企业微信](/04-department-efficiency-wecom.gif)

**提示词：** `整理出部门的效率，将数据发送到企业微信，部门效率计算公式如下：效率 = 任务 bid / timelog 工时`
