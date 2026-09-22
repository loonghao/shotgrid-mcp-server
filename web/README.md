# MCP Apps UI sources (development only)

These are the Vite + TypeScript sources for the ShotGrid status dashboard UI
shipped by `shotgrid_mcp_server.apps.dashboard`.

**Node is a development-time tool only.** The runtime dependency graph, the
published wheel, and `pyproject.toml` have no Node dependency. The build output
is a single self-contained HTML file that is committed to the repository:

```text
web/  --npm run build-->  src/shotgrid_mcp_server/apps/dashboard/index.html
```

## Build

```bash
npm install
npm run build
```

Commit the rebuilt `index.html`. CI and end users do not need Node.

## Why a single file?

MCP Apps hosts render `ui://` resources in a sandboxed iframe with a
default-deny CSP, so the UI cannot load external scripts or stylesheets.
`vite-plugin-singlefile` inlines everything into one document.

## Live development

```bash
npm run dev
```

`npm run dev` serves the UI with hot reload, but the app cannot complete the
`ui/initialize` handshake outside a real MCP Apps host. To exercise the full
loop, use `ext-apps/examples/basic-host` or a `cloudflared` tunnel registered
as a custom connector.
