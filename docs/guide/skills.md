# Skills

The server implements the MCP **Skills** extension
(`io.modelcontextprotocol/skills`, SEP-2640). Skills are
[Agent Skills](https://agentskills.io/specification) — a directory holding a
`SKILL.md` plus optional supporting files — exposed over MCP, so the workflow
instructions that describe how to use this server travel with the server
itself.

Everything rides on the ordinary Resources primitive: skills are discovered
with `skills/list`, resolved by URI with `skills/get`, and read with
`resources/read`.

## What the server ships

Three skills are bundled in `src/shotgrid_mcp_server/data/skills`:

| Skill | What it covers |
|-------|----------------|
| `shotgrid-entity-search` | Picking the right search tool and writing correct filters |
| `shotgrid-task-management` | Reading, updating and batching tasks without clobbering fields |
| `shotgrid-schema-discovery` | Resolving entity types, field names and status codes before writing |

Each ships a second file under `references/`, so a host can prove the manifest
mechanism on a skill with more than one file.

## Adding your own skills

Point `SHOTGRID_MCP_SKILLS_DIR` at one or more directories, separated by `;` on
Windows and `:` elsewhere. Each direct child directory holding a `SKILL.md`
becomes a skill:

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

Every `SKILL.md` must start with YAML frontmatter carrying `name` and
`description`, and `name` must equal the directory's name. A directory that
breaks that rule is skipped with a log line rather than served half-broken, so
check the server log if a skill does not appear.

Bundled skills are scanned first. A skill with the same name in a
user-supplied root never replaces a bundled one.

## Limits

SEP-2640 asks servers to stay within **512 files** and **16 MiB** per skill.
The server serves larger skills but logs a warning, because a conforming host
is no longer obliged to load them.

## Verification

The manifest is computed from the exact bytes the server serves, so a host can
verify every file it reads by `size` and SHA-256 `digest`, and compare the
`SKILL.md` frontmatter field-by-field. Text files are served byte for byte —
a skill authored with CRLF line endings is served with CRLF.

To reproduce the end-to-end evidence against a live server:

```bash
uv run python scripts/verify_skills_extension.py
```

The script starts the real server over HTTP, drives it with raw JSON-RPC, and
prints the `server/discover`, `skills/list`, `skills/get` and `resources/read`
responses together with a list of contract violations (empty when everything
passes).

## Host support

**Server-side support is complete and conformant.** Host support for Skills
over MCP is still rolling out across MCP clients; a host that does not
implement the extension simply never calls `skills/list` or `skills/get` and
sees no change. The extension is advertised on the modern `server/discover`
path:

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

The legacy `initialize` handshake predates extensions and does not carry a
`capabilities.extensions` field. Its absence there is expected, not a defect.

`directoryRead` is `false`: the server does not implement
`resources/directory/read`. Every file of a skill is listed by `resources/list`
and individually addressable, so a host can navigate a skill from the manifest
without directory reads.
