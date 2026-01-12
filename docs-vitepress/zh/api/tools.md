# 工具概览

ShotGrid MCP Server 提供 **40+ 工具** 用于与 ShotGrid 交互。

## 工具分类

| 分类 | 工具数 | 描述 |
|------|--------|------|
| **CRUD** | 5 | 创建、读取、更新、删除实体 |
| **批量操作** | 3 | 高效的批量操作 |
| **媒体** | 2 | 缩略图上传/下载 |
| **笔记** | 3 | 创建、读取、更新笔记 |
| **播放列表** | 2+ | 播放列表管理 |
| **直接 API** | 10+ | 底层 ShotGrid API 访问 |

## CRUD 操作

| 工具 | 描述 |
|------|------|
| `create_entity` | 创建新实体 |
| `find_one_entity` | 查找单个实体 |
| `search_entities` | 搜索多个实体 |
| `update_entity` | 更新现有实体 |
| `delete_entity` | 删除实体 |

## 批量操作

| 工具 | 描述 |
|------|------|
| `batch_create` | 一次创建多个实体 |
| `batch_update` | 一次更新多个实体 |
| `batch_delete` | 一次删除多个实体 |

## 媒体操作

| 工具 | 描述 |
|------|------|
| `download_thumbnail` | 下载实体缩略图 |
| `upload_thumbnail` | 上传实体缩略图 |

## 笔记

| 工具 | 描述 |
|------|------|
| `shotgrid.note.create` | 创建新笔记 |
| `shotgrid.note.read` | 读取笔记内容 |
| `shotgrid.note.update` | 更新现有笔记 |

## 播放列表

| 工具 | 描述 |
|------|------|
| `create_playlist` | 创建新播放列表 |
| `find_playlists` | 查找播放列表 |

## 直接 API

| 工具 | 描述 |
|------|------|
| `sg.find` | 直接 ShotGrid 查找 |
| `sg.create` | 直接 ShotGrid 创建 |
| `sg.update` | 直接 ShotGrid 更新 |
| `sg.batch` | 直接 ShotGrid 批量操作 |
| `sg.schema` | 获取实体 Schema |
