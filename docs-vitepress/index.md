---
layout: home

hero:
  name: "ShotGrid MCP Server"
  text: "AI-Powered ShotGrid Integration"
  tagline: A Model Context Protocol server for Autodesk ShotGrid/Flow Production Tracking
  image:
    src: /logo.png
    alt: ShotGrid MCP Server
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/loonghao/shotgrid-mcp-server

features:
  - icon: 🛠️
    title: 40+ Tools
    details: Complete CRUD operations, batch processing, thumbnails, notes, and playlists
  - icon: ⚡
    title: High Performance
    details: Connection pooling, schema caching, and lazy initialization
  - icon: 🚀
    title: Multiple Transports
    details: stdio (local), HTTP (remote), ASGI (production)
  - icon: 🐳
    title: Easy Deployment
    details: Docker, FastMCP Cloud, uvicorn/gunicorn, any ASGI server
---

## Demo

### 0. Configure ShotGrid MCP in Code Editor

![Configure ShotGrid MCP](/00-codebuddy-config-shotgrid-mcp.gif)

### 1. Query Task Schedule & Workload Visualization

![Query Task Schedule](/01-query-projects-visualize-tasks.gif)

**Prompt:** `Query the team's task schedule for the past week, calculate workload rate based on 8 hours per day, and visualize it in web format`

### 2. Batch Create Assets & Assign Tasks

![Batch Create Assets](/02-batch-create-assets-tasks-assign.gif)

**Prompt:** `Batch create the recommended hero characters in the shotgrid Demo:Animation project, categorize them as characters, use the FilmVFX-CharacterAsset task template, assign tasks to Yang Zhuo, with start and end dates set to next week`

### 3. TimeLog Statistics & Visualization

![TimeLog Statistics](/03-timelog-statistics-visualize.gif)

**Prompt:** `Query timelog data from shotgrid and visualize it in web format`

### 4. Department Efficiency Statistics & Send to WeCom

![Department Efficiency](/04-department-efficiency-wecom.gif)

**Prompt:** `Calculate department efficiency and send the data to WeCom. Efficiency formula: Efficiency = Task bid / Timelog hours`
