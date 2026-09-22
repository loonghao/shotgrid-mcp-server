#!/usr/bin/env python
"""End-to-end verification of the MCP Skills extension against a live server.

Starts the real ShotGrid MCP server over the Streamable HTTP transport and
drives it with raw JSON-RPC, so the evidence is the bytes a host would see
rather than a client library's interpretation of them.

Usage::

    uv run python scripts/verify_skills_extension.py [--port 8765]

Prints a JSON report to stdout and exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MODERN_PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSION = "2025-06-18"


def _free_port() -> int:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD")):  # noqa: S310
                pass
        except urllib.error.HTTPError:
            return  # the endpoint answered; a 4xx on HEAD is fine
        except OSError:
            time.sleep(0.2)
        else:
            return
    raise RuntimeError(f"server did not start at {url}")


class _RawMCPClient:
    """A deliberately dumb JSON-RPC client: no SDK, no interpretation."""

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._id = 0
        self.session_id: str | None = None

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        protocol_version: str | None = None,
    ) -> dict[str, Any]:
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if protocol_version:
            # The 2026-07-28 HTTP transport validates these routing headers
            # against the body before dispatching.
            headers["MCP-Protocol-Version"] = protocol_version
            headers["MCP-Method"] = method
            name_key = {"tools/call": "name", "prompts/get": "name", "resources/read": "uri"}.get(method)
            if name_key and body["params"].get(name_key) is not None:
                headers["MCP-Name"] = str(body["params"][name_key])
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        raw = urllib.request.Request(  # noqa: S310
            self._endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(raw) as response:  # noqa: S310
                session = response.headers.get("Mcp-Session-Id")
                if session:
                    self.session_id = session
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            # The error body carries the JSON-RPC error; surface it verbatim.
            detail = error.read().decode("utf-8", errors="replace").strip()
            try:
                return json.loads(detail)
            except json.JSONDecodeError:
                return {"http_error": error.code, "body": detail}

        return _first_json(payload)

    def envelope_request(
        self, method: str, params: dict[str, Any], protocol_version: str = MODERN_PROTOCOL_VERSION
    ) -> dict[str, Any]:
        """Send a 2026-07-28 request carrying its own envelope in ``_meta``."""
        return self.request(
            method,
            {
                **params,
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": protocol_version,
                    "io.modelcontextprotocol/clientInfo": {"name": "verify-skills", "version": "1.0.0"},
                    "io.modelcontextprotocol/clientCapabilities": {
                        "extensions": {"io.modelcontextprotocol/skills": {}}
                    },
                },
            },
            protocol_version=protocol_version,
        )


def _first_json(payload: str) -> dict[str, Any]:
    """Pull the first JSON object out of a plain or SSE response body."""
    text = payload.strip()
    if text.startswith("{"):
        return json.loads(text)
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    raise RuntimeError(f"no JSON-RPC message in response: {payload!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--output", default=None, help="also write the JSON report to this path")
    args = parser.parse_args()

    port = args.port or _free_port()
    endpoint = f"http://127.0.0.1:{port}{args.path}"

    env_import = (
        "import os;"
        "os.environ.setdefault('SHOTGRID_URL','https://example.shotgrid.autodesk.com');"
        "os.environ.setdefault('SHOTGRID_SCRIPT_NAME','verify');"
        "os.environ.setdefault('SHOTGRID_SCRIPT_KEY','verify')"
    )
    command = [
        sys.executable,
        "-c",
        f"{env_import};"
        "from shotgrid_mcp_server.server import create_server;"
        "create_server(lazy_connection=True, preload_schema=False).run("
        f"transport='http', host='127.0.0.1', port={port}, path={args.path!r})",
    ]

    process = subprocess.Popen(
        command,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_lines: list[str] = []
    pump = threading.Thread(target=lambda: log_lines.extend(_pump(process)), daemon=True)

    results: dict[str, Any] = {}
    failures: list[str] = []
    try:
        pump.start()
        _wait_for_server(endpoint)
        client = _RawMCPClient(endpoint)
        checks = {
            # server/discover is a 2026-07-28 method: the request carries its
            # own envelope in _meta instead of relying on a handshake.
            "server/discover": lambda: client.envelope_request("server/discover", {}),
            "initialize (legacy)": lambda: client.request(
                "initialize",
                {
                    "protocolVersion": LEGACY_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "verify-skills", "version": "1.0.0"},
                },
            ),
            "resources/list": lambda: client.envelope_request("resources/list", {}),
            "skills/list": lambda: client.envelope_request("skills/list", {}),
            "skills/get": lambda: client.envelope_request(
                "skills/get", {"uri": "skill://shotgrid-entity-search/SKILL.md"}
            ),
            "skills/get (unknown)": lambda: client.envelope_request("skills/get", {"uri": "skill://nope/SKILL.md"}),
            "resources/read": lambda: client.envelope_request(
                "resources/read", {"uri": "skill://shotgrid-entity-search/SKILL.md"}
            ),
            "resources/read (supporting file)": lambda: client.envelope_request(
                "resources/read", {"uri": "skill://shotgrid-entity-search/references/filters.md"}
            ),
            "resources/read (shotgrid schema)": lambda: client.envelope_request(
                "resources/read", {"uri": "shotgrid://schema/statuses"}
            ),
        }
        for name, call in checks.items():
            try:
                results[name] = call()
            except Exception as exc:  # noqa: BLE001 - a failed call is evidence, not a crash
                results[name] = {"transport_error": str(exc)}

        failures = _evaluate(results)
    finally:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()

    report = {"endpoint": endpoint, "results": results, "failures": failures}
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    if failures:
        print("\nFAILED CHECKS:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
    return 1 if failures else 0


def _pump(process: subprocess.Popen[str]) -> list[str]:
    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        lines.append(line.rstrip())
    return lines


def _check_discovery(results: dict[str, Any]) -> list[str]:
    """The extension and the resources capability are advertised on server/discover."""
    failures: list[str] = []
    discover = results["server/discover"].get("result", {}).get("capabilities", {})
    extensions = discover.get("extensions") or {}

    if "io.modelcontextprotocol/skills" not in extensions:
        failures.append("server/discover does not advertise io.modelcontextprotocol/skills")
    elif extensions["io.modelcontextprotocol/skills"].get("directoryRead") is not False:
        failures.append("skills settings do not declare directoryRead: false")
    if "resources" not in discover:
        failures.append("server/discover does not advertise the resources capability")
    return failures


def _check_listing(listing: dict[str, Any]) -> list[str]:
    """skills/list answers with complete, cacheable, verifiable entries."""
    failures: list[str] = []

    if listing.get("resultType") != "complete":
        failures.append("skills/list resultType is not 'complete'")
    for field in ("ttlMs", "cacheScope"):
        if field not in listing:
            failures.append(f"skills/list is missing {field}")
    if listing.get("cacheScope") not in ("public", "private"):
        failures.append(f"skills/list cacheScope {listing.get('cacheScope')!r} is not public/private")

    skills = listing.get("skills") or []
    if not skills:
        failures.append("skills/list returned no skills")
    for skill in skills:
        failures.extend(_check_entry(skill))
    return failures


def _check_entry(skill: dict[str, Any]) -> list[str]:
    """One skill entry: identity, frontmatter, and a complete manifest."""
    failures: list[str] = []
    uri = skill.get("uri", "")
    frontmatter = skill.get("frontmatter", {})

    if not frontmatter.get("name") or not frontmatter.get("description"):
        failures.append(f"{uri}: frontmatter missing name/description")
    if uri.rsplit("/", 1)[-1] != "SKILL.md" or uri.rsplit("/", 2)[-2] != frontmatter.get("name"):
        failures.append(f"{uri}: final path segment does not match frontmatter name")

    manifest = skill.get("resources")
    if not isinstance(manifest, list) or not manifest:
        failures.append(f"{uri}: resources manifest is missing or empty")
        return failures

    if len(manifest) > 512:
        failures.append(f"{uri}: manifest exceeds the 512-file limit")
    if manifest[0].get("uri") != uri:
        failures.append(f"{uri}: manifest does not lead with SKILL.md")
    for item in manifest:
        digest = str(item.get("digest", ""))
        if not digest.startswith("sha256:") or len(digest) != 71:
            failures.append(f"{uri}: manifest digest {digest!r} is not sha256:<64 hex>")
        if not isinstance(item.get("size"), int) or item["size"] < 0:
            failures.append(f"{uri}: manifest size {item.get('size')!r} is not a byte count")
    return failures


def _check_retrieval(results: dict[str, Any], listing: dict[str, Any]) -> list[str]:
    """skills/get mirrors the listing and rejects unknown URIs with -32602."""
    failures: list[str] = []
    single = results["skills/get"].get("result", {})
    skills = listing.get("skills") or []

    if single.get("resultType") != "complete":
        failures.append("skills/get resultType is not 'complete'")
    for field in ("ttlMs", "cacheScope"):
        if field not in single:
            failures.append(f"skills/get is missing {field}")
    if not single.get("skill", {}).get("uri"):
        failures.append("skills/get did not return a skill entry")
    if skills and single.get("skill", {}).get("uri") != skills[0].get("uri"):
        failures.append("skills/get entry does not match the listing entry")

    unknown = results["skills/get (unknown)"].get("error", {})
    if unknown.get("code") != -32602:
        failures.append(f"unknown skill URI returned {unknown.get('code')!r}, expected -32602")
    return failures


def _check_content(results: dict[str, Any], listing: dict[str, Any]) -> list[str]:
    """resources/read serves the bytes the manifest describes."""
    failures: list[str] = []
    skills = listing.get("skills") or []
    contents = results["resources/read"].get("result", {}).get("contents") or []

    if not contents or not contents[0].get("text", "").startswith("---"):
        failures.append("resources/read of SKILL.md did not return frontmatter text")
        return failures

    if contents[0].get("mimeType") != "text/markdown":
        failures.append(f"SKILL.md mimeType is {contents[0].get('mimeType')!r}, expected text/markdown")

    expected_size = skills[0]["resources"][0]["size"] if skills else -1
    actual_size = len(contents[0]["text"].encode("utf-8"))
    if expected_size != actual_size:
        failures.append(f"SKILL.md served {actual_size} bytes, manifest says {expected_size}")

    if not results["resources/read (supporting file)"].get("result", {}).get("contents"):
        failures.append("resources/read of a supporting file returned nothing")
    if results["resources/read (shotgrid schema)"].get("result", {}).get("contents") is None:
        failures.append("shotgrid://schema/* is no longer readable alongside skill:// resources")

    listed = results["resources/list"].get("result", {}).get("resources", [])
    listed_uris = {resource.get("uri") for resource in listed}
    for skill in skills:
        if skill["uri"] not in listed_uris:
            failures.append(f"{skill['uri']} is not enumerable through resources/list")
    return failures


def _evaluate(results: dict[str, Any]) -> list[str]:
    """Assert the SEP-2640 contract against the raw responses."""
    listing = results["skills/list"].get("result", {})
    return [
        *_check_discovery(results),
        *_check_listing(listing),
        *_check_retrieval(results, listing),
        *_check_content(results, listing),
    ]


if __name__ == "__main__":
    raise SystemExit(main())
