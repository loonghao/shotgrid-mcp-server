# 笔记与播放列表

在 ShotGrid 中管理笔记和播放列表。

## 笔记

### shotgrid.note.create

在实体上创建新笔记。

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `project_id` | number | 是 | 项目 ID |
| `entity_type` | string | 是 | 关联的实体类型 |
| `entity_id` | number | 是 | 关联的实体 ID |
| `subject` | string | 否 | 笔记主题 |
| `content` | string | 是 | 笔记内容 |
| `addressings_to` | array | 否 | 要通知的用户 |

#### 示例

```
在镜头 456 上添加笔记："动画已批准，准备进入灯光阶段"
```

### shotgrid.note.read

读取笔记内容。

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `note_id` | number | 是 | 笔记 ID |

#### 示例

```
读取笔记 789
```

### shotgrid.note.update

更新现有笔记。

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `note_id` | number | 是 | 笔记 ID |
| `content` | string | 否 | 新内容 |
| `subject` | string | 否 | 新主题 |

#### 示例

```
用新内容更新笔记 789
```

## 播放列表

### create_playlist

创建用于审阅的新播放列表。

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `project_id` | number | 是 | 项目 ID |
| `code` | string | 是 | 播放列表名称 |
| `versions` | array | 否 | 要包含的版本 ID |

#### 示例

```
创建名为 "每日审阅" 的播放列表，包含版本 100、101、102
```

### find_playlists

查找匹配条件的播放列表。

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `project_id` | number | 否 | 按项目过滤 |
| `filters` | array | 否 | 其他过滤条件 |

#### 示例

```
查找项目 123 中的所有播放列表
```
