"""Tests for the MCP Skills extension (SEP-2640)."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client, FastMCP
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS

from shotgrid_mcp_server.skills_extension import (
    DEFAULT_CACHE_SCOPE,
    DEFAULT_TTL_MS,
    MAX_SKILL_FILES,
    SKILLS_EXTENSION_ID,
    SkillCatalog,
    SkillsExtension,
    SkillsGetParams,
    SkillsListParams,
    bundled_skills_dir,
    default_skill_roots,
    register_skills,
)

SKILL_MD = """---
name: {name}
description: {description}
---

# {name}

Body text.
"""

# Extension method handlers ignore the request context; None stands in for it.
_NO_CONTEXT = None


def _write(path: Path, content: str) -> None:
    """Write text without newline translation, so tests control the bytes."""
    path.write_bytes(content.encode("utf-8"))


def _write_skill(
    root: Path, name: str, *, description: str = "A test skill", extra_files: dict[str, str] | None = None
):
    """Create a valid skill directory and return its path."""
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    _write(skill_dir / "SKILL.md", SKILL_MD.format(name=name, description=description))
    for relative_path, content in (extra_files or {}).items():
        target = skill_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        _write(target, content)
    return skill_dir


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(skill_name: str, uri: str) -> str:
    return uri.split(f"skill://{skill_name}/", 1)[1]


def _list(catalog: SkillCatalog, cursor: str | None = None) -> Any:
    return asyncio.run(SkillsExtension(catalog)._on_list(_NO_CONTEXT, SkillsListParams(cursor=cursor)))


def _get(catalog: SkillCatalog, uri: str) -> Any:
    return asyncio.run(SkillsExtension(catalog)._on_get(_NO_CONTEXT, SkillsGetParams(uri=uri)))


# ---------------------------------------------------------------------------
# Bundled skills
# ---------------------------------------------------------------------------


def test_bundled_skills_load_and_satisfy_the_spec() -> None:
    """Every bundled skill is a valid Agent Skill publishable over MCP."""
    catalog = SkillCatalog(bundled_skills_dir())

    assert catalog.skills, "the package ships no skills"
    assert catalog.skipped == ()

    for skill in catalog.skills:
        # SEP-2640: the final segment of the SKILL.md parent path equals name.
        assert skill.uri == f"skill://{skill.name}/SKILL.md"
        assert skill.frontmatter["name"] == skill.name
        assert skill.frontmatter["description"]

        # The manifest leads with SKILL.md and covers every file exactly once.
        assert skill.files[0].uri == skill.uri
        assert len({file.uri for file in skill.files}) == len(skill.files)
        assert len(skill.files) <= MAX_SKILL_FILES
        for file in skill.files:
            assert file.digest.startswith("sha256:") and len(file.digest) == 71
            on_disk = skill.path / _relative(skill.name, file.uri)
            assert file.size == on_disk.stat().st_size


def test_bundled_skill_digests_cover_the_served_bytes() -> None:
    """Digests and sizes are taken over the raw bytes a host receives."""
    catalog = SkillCatalog(bundled_skills_dir())

    for skill in catalog.skills:
        for file in skill.files:
            on_disk = skill.path / _relative(skill.name, file.uri)
            assert file.digest == _sha256(on_disk)
            assert file.size == len(on_disk.read_bytes())


def test_default_roots_start_with_the_bundled_directory() -> None:
    """Bundled roots are scanned first so extras cannot shadow them."""
    assert default_skill_roots()[0] == bundled_skills_dir()


def test_default_roots_include_configured_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SHOTGRID_MCP_SKILLS_DIR adds roots, pathsep separated."""
    _write_skill(tmp_path, "studio-custom")
    monkeypatch.setenv("SHOTGRID_MCP_SKILLS_DIR", f"{tmp_path}{os.pathsep}{tmp_path / 'missing'}")

    roots = default_skill_roots()
    assert roots[0] == bundled_skills_dir()
    assert tmp_path.resolve() in roots
    assert (tmp_path / "missing").resolve() in roots


# ---------------------------------------------------------------------------
# Validation and skipping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scenario",
    ["no_frontmatter", "no_name", "no_description", "name_mismatch", "bad_name", "no_skill_md"],
)
def test_invalid_skill_directories_are_skipped(tmp_path: Path, scenario: str) -> None:
    """A directory that is not a servable skill never reaches the catalog."""
    name = "broken-skill" if scenario != "bad_name" else "Bad_Name"
    _write_skill(tmp_path, name)

    if scenario == "no_frontmatter":
        _write(tmp_path / name / "SKILL.md", "# No frontmatter\n")
    elif scenario == "no_name":
        _write(tmp_path / name / "SKILL.md", "---\ndescription: x\n---\n")
    elif scenario == "no_description":
        _write(tmp_path / name / "SKILL.md", f"---\nname: {name}\n---\n")
    elif scenario == "name_mismatch":
        _write(tmp_path / name / "SKILL.md", "---\nname: another-name\ndescription: x\n---\n")
    elif scenario == "no_skill_md":
        (tmp_path / name / "SKILL.md").unlink()

    catalog = SkillCatalog(tmp_path)
    assert catalog.skills == ()
    assert catalog.skipped, f"{scenario} should have been skipped with a reason"


def test_frontmatter_ending_at_end_of_file_is_parsed(tmp_path: Path) -> None:
    """A SKILL.md whose frontmatter ends at EOF is valid, not 'no frontmatter'.

    Regression: the closing-delimiter regex required a newline after the final
    ``---``, so a file ending exactly at the delimiter was skipped with the
    misleading reason "has no YAML frontmatter".
    """
    skill_dir = _write_skill(tmp_path, "eof-skill")
    _write(skill_dir / "SKILL.md", "---\nname: eof-skill\ndescription: Ends at the delimiter\n---")

    catalog = SkillCatalog(tmp_path)

    assert catalog.skipped == ()
    (skill,) = catalog.skills
    assert skill.frontmatter == {"name": "eof-skill", "description": "Ends at the delimiter"}


def test_files_outside_the_skill_directory_are_not_manifested(tmp_path: Path) -> None:
    """A symlink escaping the skill directory is dropped, not published."""
    skill_dir = _write_skill(tmp_path, "escaping-skill")
    outside = tmp_path / "outside.md"
    _write(outside, "secret")

    try:
        (skill_dir / "link.md").symlink_to(outside)
    except (OSError, NotImplementedError):  # pragma: no cover - unprivileged Windows
        pytest.skip("symlinks are not available")

    catalog = SkillCatalog(tmp_path)
    assert len(catalog.skills) == 1
    assert all(not file.uri.endswith("link.md") for file in catalog.skills[0].files)


def test_hidden_and_cache_directories_are_ignored(tmp_path: Path) -> None:
    """Cruft in a skill directory does not become part of the manifest."""
    _write_skill(
        tmp_path,
        "tidy-skill",
        extra_files={".hidden.md": "x", "__pycache__/stale.md": "y", "references/keep.md": "z"},
    )

    catalog = SkillCatalog(tmp_path)
    uris = [file.uri for file in catalog.skills[0].files]

    assert "skill://tidy-skill/references/keep.md" in uris
    assert not any(".hidden" in uri or "__pycache__" in uri for uri in uris)


def test_reserved_manifest_file_name_is_skipped(tmp_path: Path) -> None:
    """A file named _manifest cannot shadow the synthetic resource."""
    _write_skill(tmp_path, "reserved-skill", extra_files={"_manifest": "{}"})

    catalog = SkillCatalog(tmp_path)
    assert all(not file.uri.endswith("_manifest") for file in catalog.skills[0].files)


@pytest.mark.asyncio
async def test_crlf_skill_is_served_byte_for_byte(tmp_path: Path) -> None:
    """A CRLF-authored skill is served with CRLF, so its manifest verifies.

    Regression: serving text through universal-newline translation changed the
    bytes on the wire, so a host comparing size and digest would reject every
    skill authored on Windows.
    """
    skill_dir = tmp_path / "crlf-skill"
    skill_dir.mkdir()
    _write(
        skill_dir / "SKILL.md",
        "---\r\nname: crlf-skill\r\ndescription: Authored with CRLF\r\n---\r\n\r\n# crlf-skill\r\n",
    )

    server: FastMCP = FastMCP(name="test")
    extension = register_skills(server, roots=[tmp_path])
    (skill,) = extension.catalog.skills
    (manifest_file,) = skill.files

    assert manifest_file.size == len((skill_dir / "SKILL.md").read_bytes())

    async with Client(server) as client:
        (block,) = await client.read_resource(skill.uri)
        raw = block.text.encode("utf-8")  # type: ignore[union-attr]
        assert b"\r\n" in raw
        assert len(raw) == manifest_file.size
        assert hashlib.sha256(raw).hexdigest() == manifest_file.digest.removeprefix("sha256:")


@pytest.mark.asyncio
async def test_non_utf8_text_file_is_served_as_a_blob(tmp_path: Path) -> None:
    """A text/* file that is not UTF-8 is delivered as base64, not an error.

    Regression: ``read()`` decoded every text/* file as UTF-8, so a latin-1
    reference file turned ``resources/read`` into a UnicodeDecodeError while
    the manifest still advertised the bytes as deliverable.
    """
    skill_dir = _write_skill(tmp_path, "latin-skill")
    (skill_dir / "references").mkdir()
    legacy = "# Caf\u00e9 filters\n".encode("latin-1")  # 0xe9 is not valid UTF-8
    (skill_dir / "references" / "legacy.md").write_bytes(legacy)
    uri = "skill://latin-skill/references/legacy.md"

    server: FastMCP = FastMCP(name="test")
    extension = register_skills(server, roots=[tmp_path])
    (skill,) = extension.catalog.skills
    (entry,) = [file for file in skill.files if file.uri == uri]

    async with Client(server) as client:
        (block,) = await client.read_resource(uri)
        served = base64.b64decode(block.blob)  # type: ignore[union-attr]
        assert served == legacy
        assert len(served) == entry.size
        assert hashlib.sha256(served).hexdigest() == entry.digest.removeprefix("sha256:")


def test_supporting_files_are_manifested(tmp_path: Path) -> None:
    """A skill's references are part of the manifest, SKILL.md first."""
    skill_dir = _write_skill(tmp_path, "with-refs", extra_files={"references/guide.md": "guide"})

    catalog = SkillCatalog(tmp_path)
    (skill,) = catalog.skills
    entry = skill.entry()

    assert entry.uri == "skill://with-refs/SKILL.md"
    assert [file.uri for file in entry.resources] == [
        "skill://with-refs/SKILL.md",
        "skill://with-refs/references/guide.md",
    ]
    assert entry.resources[1].size == len("guide")
    assert entry.resources[1].digest == _sha256(skill_dir / "references" / "guide.md")


def test_first_root_wins_on_duplicate_skill_names(tmp_path: Path) -> None:
    """A same-named skill from a later root cannot shadow an earlier one."""
    first, second = tmp_path / "first", tmp_path / "second"
    _write_skill(first, "shared-name", description="from the first root")
    _write_skill(second, "shared-name", description="from the second root")

    catalog = SkillCatalog([first, second])
    assert len(catalog.skills) == 1
    assert catalog.skills[0].frontmatter["description"] == "from the first root"


def test_missing_root_is_ignored(tmp_path: Path) -> None:
    """A configured root that does not exist is not an error."""
    catalog = SkillCatalog([tmp_path / "nope"])
    assert catalog.skills == ()
    assert catalog.skipped == ()


def test_refresh_picks_up_a_new_skill(tmp_path: Path) -> None:
    """refresh() rebuilds the snapshot in place."""
    catalog = SkillCatalog(tmp_path)
    assert catalog.skills == ()

    _write_skill(tmp_path, "late-skill")
    catalog.refresh()
    assert [skill.name for skill in catalog.skills] == ["late-skill"]


# ---------------------------------------------------------------------------
# Listing and retrieval
# ---------------------------------------------------------------------------


def test_list_carries_the_caching_attributes(tmp_path: Path) -> None:
    """skills/list answers with resultType, ttlMs and cacheScope."""
    _write_skill(tmp_path, "alpha-skill")
    catalog = SkillCatalog(tmp_path, ttl_ms=1234)

    result = _list(catalog)

    assert result.result_type == "complete"
    assert result.ttl_ms == 1234
    assert result.cache_scope in ("public", "private")
    assert result.next_cursor is None
    assert [entry.uri for entry in result.skills] == ["skill://alpha-skill/SKILL.md"]


def test_list_defaults_come_from_the_module(tmp_path: Path) -> None:
    """A catalog built without overrides uses the documented defaults."""
    _write_skill(tmp_path, "defaulted-skill")
    result = _list(SkillCatalog(tmp_path))

    assert result.ttl_ms == DEFAULT_TTL_MS
    assert result.cache_scope == DEFAULT_CACHE_SCOPE


def test_list_pagination_walks_every_skill_exactly_once(tmp_path: Path) -> None:
    """An entry is atomic: paging never splits or repeats a skill."""
    for index in range(5):
        _write_skill(tmp_path, f"skill-{index}")
    catalog = SkillCatalog(tmp_path, page_size=2)

    seen: list[str] = []
    cursor: str | None = None
    for _ in range(10):
        result = _list(catalog, cursor)
        seen.extend(entry.uri for entry in result.skills)
        cursor = result.next_cursor
        if cursor is None:
            break

    assert len(seen) == 5
    assert len(set(seen)) == 5
    assert seen == sorted(seen)


def test_list_rejects_a_corrupt_cursor(tmp_path: Path) -> None:
    """A cursor the server did not issue is INVALID_PARAMS, not a crash."""
    _write_skill(tmp_path, "cursor-skill")
    with pytest.raises(MCPError) as raised:
        _list(SkillCatalog(tmp_path), cursor="not-a-cursor")

    assert raised.value.code == INVALID_PARAMS


def test_get_resolves_a_skill_by_its_skill_md_uri(tmp_path: Path) -> None:
    """skills/get answers for every skill it serves, listing or not."""
    _write_skill(tmp_path, "direct-skill")
    result = _get(SkillCatalog(tmp_path), "skill://direct-skill/SKILL.md")

    assert result.result_type == "complete"
    assert result.skill.uri == "skill://direct-skill/SKILL.md"
    assert result.ttl_ms == DEFAULT_TTL_MS
    assert result.cache_scope == DEFAULT_CACHE_SCOPE


def test_get_resolves_a_supporting_file_uri_to_its_skill(tmp_path: Path) -> None:
    """A supporting-file URI still yields the entry needed to verify the read."""
    _write_skill(tmp_path, "ref-skill", extra_files={"references/guide.md": "guide"})
    result = _get(SkillCatalog(tmp_path), "skill://ref-skill/references/guide.md")

    assert result.skill.uri == "skill://ref-skill/SKILL.md"


def test_get_rejects_an_unknown_uri_with_invalid_params(tmp_path: Path) -> None:
    """SEP-2640: an unknown skill URI is -32602, not a server error."""
    _write_skill(tmp_path, "known-skill")
    with pytest.raises(MCPError) as raised:
        _get(SkillCatalog(tmp_path), "skill://unknown-skill/SKILL.md")

    assert raised.value.code == INVALID_PARAMS


def test_get_rejects_a_non_skill_uri(tmp_path: Path) -> None:
    """A URI outside the skill:// namespace is unknown, not a crash."""
    with pytest.raises(MCPError) as raised:
        _get(SkillCatalog(tmp_path), "shotgrid://schema/statuses")

    assert raised.value.code == INVALID_PARAMS


# ---------------------------------------------------------------------------
# Extension wiring
# ---------------------------------------------------------------------------


def test_extension_advertises_its_identifier_and_settings(tmp_path: Path) -> None:
    """The extension contributes both methods and a negotiated capability."""
    _write_skill(tmp_path, "wired-skill")
    extension = SkillsExtension(SkillCatalog(tmp_path), directory_read=False)

    assert extension.identifier == SKILLS_EXTENSION_ID
    assert extension.settings() == {"directoryRead": False}
    assert [binding.method for binding in extension.methods()] == ["skills/list", "skills/get"]
    assert SkillsExtension(SkillCatalog(tmp_path), directory_read=True).settings() == {"directoryRead": True}


def test_register_skills_installs_resources_and_extension(tmp_path: Path) -> None:
    """Registration adds the skill resources and the extension in one step."""
    _write_skill(tmp_path, "registered-skill", extra_files={"references/guide.md": "guide"})
    (tmp_path / "not-a-skill").mkdir()

    server: FastMCP = FastMCP(name="test")
    extension = register_skills(server, roots=[tmp_path], ttl_ms=99)

    assert [skill.name for skill in extension.catalog.skills] == ["registered-skill"]
    assert len(extension.catalog.skipped) == 1
    assert extension.identifier == SKILLS_EXTENSION_ID
    assert extension.catalog.ttl_ms == 99


@pytest.mark.asyncio
async def test_registered_server_serves_skill_resources(tmp_path: Path) -> None:
    """A registered server answers resources/read for every manifest URI."""
    _write_skill(tmp_path, "served-skill", extra_files={"references/guide.md": "guide"})

    server: FastMCP = FastMCP(name="test")
    extension = register_skills(server, roots=[tmp_path])
    (skill,) = extension.catalog.skills

    async with Client(server) as client:
        listed = {str(resource.uri) for resource in await client.list_resources()}
        assert listed.issuperset(file.uri for file in skill.files)

        for file in skill.files:
            (block,) = await client.read_resource(file.uri)
            raw = (block.text or "").encode("utf-8") if hasattr(block, "text") else block.blob  # type: ignore[union-attr]
            assert len(raw) == file.size, f"{file.uri} size mismatch"
            assert hashlib.sha256(raw).hexdigest() == file.digest.removeprefix("sha256:"), f"{file.uri} digest mismatch"

        (body,) = await client.read_resource(skill.uri)
        assert body.text.startswith("---\nname: served-skill\n")


@pytest.mark.asyncio
async def test_skill_resources_coexist_with_shotgrid_resources(tmp_path: Path) -> None:
    """skill:// resources do not disturb the existing shotgrid:// resources."""
    _write_skill(tmp_path, "coexisting-skill")

    server: FastMCP = FastMCP(name="test")

    @server.resource("shotgrid://schema/statuses")
    def schema_statuses() -> dict[str, Any]:
        return {"Asset": {"sg_status_list": {"valid_values": ["ip", "fin"]}}}

    register_skills(server, roots=[tmp_path])

    async with Client(server) as client:
        uris = {str(resource.uri) for resource in await client.list_resources()}
        assert "shotgrid://schema/statuses" in uris
        assert "skill://coexisting-skill/SKILL.md" in uris

        (statuses,) = await client.read_resource("shotgrid://schema/statuses")
        assert "sg_status_list" in statuses.text  # type: ignore[union-attr]


def test_server_capabilities_include_the_extension(tmp_path: Path) -> None:
    """The extension is advertised under capabilities.extensions."""
    _write_skill(tmp_path, "capability-skill")
    server: FastMCP = FastMCP(name="test")
    register_skills(server, roots=[tmp_path])

    capabilities = server._mcp_server.get_capabilities(protocol_version="2026-07-28")
    extensions = capabilities.extensions or {}

    assert SKILLS_EXTENSION_ID in extensions
    assert extensions[SKILLS_EXTENSION_ID] == {"directoryRead": False}
    assert capabilities.resources is not None
