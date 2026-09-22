# MCP Apps

MCP Apps let a tool return an interactive UI instead of plain text. The tool
advertises a `ui://` resource in its `_meta.ui.resourceUri`; the host fetches
that resource and renders the HTML inside a sandboxed iframe.

This server ships one app: the **ShotGrid status dashboard**.

## The dashboard tool

`shotgrid_dashboard` summarises how entities of a type are distributed across
statuses and renders the result as an interactive board.

| Argument | Type | Default | Description |
| --- | --- | --- | --- |
| `entity_type` | string | `Task` | Entity type to summarise. Common values: `Task`, `Asset`, `Shot`, `Version`, `PublishedFile`. |
| `project_id` | int \| null | `null` | Restrict the summary to one project. |
| `limit` | int | `200` | Maximum number of entities to load (1-1000). |

The tool returns a structured payload:

```json
{
  "entity_type": "Task",
  "project": null,
  "total": 4,
  "truncated": false,
  "breakdown": [
    { "status": "ip", "label": "In Progress", "count": 2, "share": 50.0 },
    { "status": "fin", "label": "Approved", "count": 1, "share": 25.0 }
  ],
  "entities": [
    { "id": 1, "label": "model", "status": "ip", "status_label": "In Progress", "detail": "model the asset" }
  ],
  "generated_at": "2026-09-22T12:00:00+00:00"
}
```

## Wire format

`tools/list` returns the UI binding on the tool:

```json
{
  "name": "shotgrid_dashboard",
  "_meta": {
    "ui": {
      "resourceUri": "ui://shotgrid/dashboard",
      "visibility": ["model", "app"]
    }
  }
}
```

`resources/read` on `ui://shotgrid/dashboard` returns the HTML document served
as `text/html;profile=mcp-app`.

## Graceful degradation

Hosts that did not negotiate the Apps extension never see the HTML. The server
detects this with `client_supports_apps()` and returns the same summary as
plain text instead:

```text
ShotGrid Task status overview — 4 entities

  In Progress: 2 (50.0%)
  Approved: 1 (25.0%)
```

## Single-file HTML

Apps render inside a CSP-restricted iframe that denies subresource loads by
default. Every script and stylesheet must therefore be inlined into one HTML
document. The dashboard is built with `vite-plugin-singlefile` and the result is
committed to `src/shotgrid_mcp_server/apps/dashboard/index.html`.

### Rebuilding the UI

Node is a **development-time** tool only. The runtime dependency graph, the
wheel, and `pyproject.toml` have no Node dependency.

```bash
cd web
npm install
npm run build
```

This writes a fresh `src/shotgrid_mcp_server/apps/dashboard/index.html`. Commit
the rebuilt file; CI and end users do not need Node.

## Verifying the integration

```bash
python scripts/verify_mcp_app.py
```

The script starts a real HTTP MCP server and drives it with raw JSON-RPC
(`initialize`, `resources/list`, `tools/list`, `resources/read`), then asserts
the tool meta, the resource MIME type, and that the bundle has no external
asset references. Pass `--no-apps` to exercise the text fallback.

## Coexistence with schema resources

The `ui://` resource is additive. The three pre-existing `shotgrid://schema/*`
resources are unaffected:

- `shotgrid://schema/entities`
- `shotgrid://schema/statuses`
- `shotgrid://schema/statuses/{entity_type}`
