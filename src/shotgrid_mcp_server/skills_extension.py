"""MCP Skills extension (SEP-2640) for the ShotGrid MCP server.

The Skills extension (``io.modelcontextprotocol/skills``) lets a server expose
workflow instructions — Agent Skills directories holding a ``SKILL.md`` plus
optional supporting files — through the ordinary Resources primitive.

Split of responsibilities:

* **Content** is served by a small resource provider that maps every file of a
  skill onto a ``skill://<name>/<path>`` resource, byte for byte.
* **Discovery** (``skills/list``) and **retrieval** (``skills/get``) are added
  as a SEP-2133 ``ServerExtension``, which also advertises the extension under
  ``capabilities.extensions`` on the modern ``server/discover`` path.

The extension publishes a manifest (``resources``) computed from the bytes it
actually serves, so a conforming host can verify every file it reads by
``size`` and SHA-256 ``digest``.

Why not ``fastmcp``'s built-in skill providers? They read text files with
``Path.read_text()``, which applies universal-newline translation, so a skill
authored with CRLF line endings is served with LF — the published digest would
then describe bytes nobody receives, and every conforming host would reject the
skill. Serving raw bytes keeps the manifest honest on every platform.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import mimetypes
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, unquote, urlsplit

# Import third-party modules
from fastmcp.resources.base import Resource
from fastmcp.server.extensions import MethodBinding, ServerExtension
from fastmcp.server.providers.base import Provider
from fastmcp.utilities.versions import VersionSpec
from mcp.server.context import ServerRequestContext
from mcp.shared.exceptions import MCPError
from mcp.types import INVALID_PARAMS, PaginatedRequestParams, RequestParams, Result, ResultType
from pydantic import AnyUrl, BaseModel, Field
from yaml import YAMLError
from yaml import load as yaml_load
from yaml.loader import BaseLoader as YamlBaseLoader

# Import local modules
from shotgrid_mcp_server.constants import ENV_SKILLS_DIRS
from shotgrid_mcp_server.tools.types import FastMCPType

logger = logging.getLogger(__name__)

#: Extension identifier negotiated under ``capabilities.extensions``.
SKILLS_EXTENSION_ID = "io.modelcontextprotocol/skills"

#: Main file every skill directory must contain (Agent Skills specification).
SKILL_MAIN_FILE = "SKILL.md"

#: Per-skill limits from SEP-2640. Hosts must accept up to these; we warn when
#: a bundled or user-provided skill exceeds them because loadability is no
#: longer guaranteed.
MAX_SKILL_FILES = 512
MAX_SKILL_BYTES = 16 * 1024 * 1024

#: Freshness hint returned with every list/get result.
DEFAULT_TTL_MS = 60_000

#: ``cacheScope`` for every result. The catalog is server-wide and contains no
#: per-caller data, so shared caching is safe.
DEFAULT_CACHE_SCOPE = "public"

#: Skills returned per ``skills/list`` page when no cursor is supplied.
DEFAULT_PAGE_SIZE = 100

_SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_RESERVED_FILE_NAMES = frozenset({"_manifest"})
_IGNORED_DIR_NAMES = frozenset({"__pycache__", ".git", ".venv", "node_modules"})

# Windows does not register .md, and a missing entry would degrade SKILL.md to
# application/octet-stream — served as base64 instead of text.
mimetypes.add_type("text/markdown", ".md")


# ---------------------------------------------------------------------------
# Wire models
# ---------------------------------------------------------------------------


class SkillFileEntry(BaseModel):
    """One file of a skill manifest (SEP-2640 ``resources[]``)."""

    uri: str
    """Resource URI of the file, readable via ``resources/read``."""

    digest: str
    """SHA-256 digest of the file's raw bytes, formatted ``sha256:<hex>``."""

    size: int
    """Length in bytes of the file's raw content (the bytes ``digest`` covers)."""


class SkillEntry(BaseModel):
    """A skill entry, identical in shape for ``skills/list`` and ``skills/get``."""

    uri: str
    """Resource URI of the skill's ``SKILL.md``."""

    frontmatter: dict[str, Any]
    """Verbatim YAML frontmatter of ``SKILL.md``, rendered as JSON."""

    resources: list[SkillFileEntry]
    """Complete file manifest, ``SKILL.md`` included."""


class SkillsListResult(Result):
    """Result of ``skills/list``."""

    result_type: ResultType = "complete"
    skills: list[SkillEntry] = Field(default_factory=list)
    ttl_ms: int = Field(default=DEFAULT_TTL_MS, ge=0)
    cache_scope: Literal["public", "private"] = Field(default=DEFAULT_CACHE_SCOPE)
    next_cursor: str | None = None


class SkillsGetResult(Result):
    """Result of ``skills/get`` — a single entry under ``skill``."""

    result_type: ResultType = "complete"
    skill: SkillEntry
    ttl_ms: int = Field(default=DEFAULT_TTL_MS, ge=0)
    cache_scope: Literal["public", "private"] = Field(default=DEFAULT_CACHE_SCOPE)


class SkillsListParams(PaginatedRequestParams):
    """``skills/list`` request params — an optional pagination cursor."""


class SkillsGetParams(RequestParams):
    """``skills/get`` request params — the URI of the skill's ``SKILL.md``."""

    uri: str


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Skill:
    """A validated skill directory."""

    name: str
    path: Path
    uri: str
    frontmatter: dict[str, Any]
    files: tuple[SkillFileEntry, ...]
    #: Absolute path of each manifest file, in the same order as ``files``.
    paths: tuple[Path, ...] = ()

    @property
    def total_bytes(self) -> int:
        return sum(file.size for file in self.files)

    def entry(self) -> SkillEntry:
        return SkillEntry(uri=self.uri, frontmatter=dict(self.frontmatter), resources=list(self.files))

    def path_for(self, uri: str) -> Path | None:
        """Absolute path of a manifest URI, or ``None`` if it is not one."""
        for entry, path in zip(self.files, self.paths, strict=True):
            if entry.uri == uri:
                return path
        return None


def _skill_file_uri(skill_name: str, relative_path: str) -> str:
    """Build the ``skill://`` URI for a file of a skill.

    Mirrors the URI shape fastmcp's ``SkillProvider`` serves, so the manifest
    this module publishes and the resources the server answers for are the
    same URIs.
    """
    return f"skill://{skill_name}/{quote(relative_path, safe='/')}"


def _compute_digest(path: Path) -> str:
    """Return the ``sha256:<hex>`` digest of a file's raw bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _iter_skill_files(skill_dir: Path) -> list[Path]:
    """List the files a skill serves, deterministically ordered.

    ``SKILL.md`` comes first, then every supporting file sorted by path.
    Hidden files, cache directories and symlinks escaping the skill directory
    are skipped.
    """
    resolved_root = skill_dir.resolve()
    files: list[Path] = []

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part in _IGNORED_DIR_NAMES for part in path.relative_to(skill_dir).parts):
            continue
        if path.name in _RESERVED_FILE_NAMES:
            logger.warning("Skipping reserved file name %s in skill %s", path.name, skill_dir.name)
            continue
        # Symlink escapes would let a manifest point outside the skill dir.
        if not path.resolve().is_relative_to(resolved_root):
            logger.warning("Skipping %s: resolves outside skill directory %s", path, skill_dir)
            continue
        files.append(path)

    main_file = skill_dir / SKILL_MAIN_FILE
    return ([main_file] if main_file in files else []) + [path for path in files if path != main_file]


def _load_skill(skill_dir: Path) -> _Skill | str:
    """Validate one skill directory.

    Returns the parsed skill, or a human-readable reason when the directory is
    not a servable skill. A skill is rejected when it has no ``SKILL.md``, when
    its frontmatter lacks ``name``/``description``, or when ``name`` does not
    match the directory's final path segment — SEP-2640 requires the final
    segment of the ``SKILL.md`` parent path to equal ``frontmatter.name``, and
    the served URI is built from that segment.
    """
    main_file = skill_dir / SKILL_MAIN_FILE
    if not main_file.is_file():
        return f"no {SKILL_MAIN_FILE} in {skill_dir.name}"

    content = main_file.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(content)
    if not frontmatter:
        return f"{skill_dir.name}/{SKILL_MAIN_FILE} has no YAML frontmatter"

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name:
        return f"{skill_dir.name}/{SKILL_MAIN_FILE} frontmatter has no 'name'"
    if not isinstance(description, str) or not description:
        return f"{skill_dir.name}/{SKILL_MAIN_FILE} frontmatter has no 'description'"
    if name != skill_dir.name:
        return f"{skill_dir.name}/{SKILL_MAIN_FILE} frontmatter name {name!r} does not match its parent directory name"
    if not _SKILL_NAME_RE.match(name):
        return f"skill name {name!r} must be lowercase letters, digits and single hyphens"

    files: list[SkillFileEntry] = []
    paths: list[Path] = []
    for path in _iter_skill_files(skill_dir):
        files.append(
            SkillFileEntry(
                uri=_skill_file_uri(name, path.relative_to(skill_dir).as_posix()),
                digest=_compute_digest(path),
                size=path.stat().st_size,
            )
        )
        paths.append(path)

    skill = _Skill(
        name=name,
        path=skill_dir,
        uri=_skill_file_uri(name, SKILL_MAIN_FILE),
        frontmatter=frontmatter,
        files=tuple(files),
        paths=tuple(paths),
    )

    if len(skill.files) > MAX_SKILL_FILES:
        logger.warning("Skill %s has %d files, over the %d-file limit", name, len(skill.files), MAX_SKILL_FILES)
    if skill.total_bytes > MAX_SKILL_BYTES:
        logger.warning("Skill %s is %d bytes, over the %d-byte limit", name, skill.total_bytes, MAX_SKILL_BYTES)

    return skill


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse the YAML frontmatter block of a ``SKILL.md``.

    Uses ``yaml.BaseLoader`` for the same reason fastmcp does: every scalar
    round-trips as written, so ``version: 1.10`` is not silently turned into
    the float ``1.1`` before it reaches a host that compares frontmatter
    field-by-field against the bytes it reads.
    """
    content = content.removeprefix("\ufeff")
    if not content.startswith("---"):
        return {}

    # The closing delimiter also ends the file when the frontmatter is
    # followed by nothing: ``---\nname: x\n---`` with no trailing newline is
    # still a frontmatter block, not a file without one.
    match = re.search(r"\n---\s*(?:\n|$)", content[3:])
    if not match:
        return {}

    try:
        parsed = yaml_load(content[3 : 3 + match.start()], Loader=YamlBaseLoader)
    except YAMLError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


class SkillCatalog:
    """An immutable, ordered snapshot of the skills this server serves.

    The snapshot is built once so that the digests published by ``skills/list``
    and ``skills/get`` stay stable for the lifetime of the server: a host binds
    approval to a manifest, and a manifest that changed underneath it would
    revoke that approval mid-session.
    """

    def __init__(
        self,
        roots: Sequence[Path | str] | Path | str,
        *,
        ttl_ms: int = DEFAULT_TTL_MS,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        self._roots = tuple(Path(root).resolve() for root in ([roots] if isinstance(roots, (str, Path)) else roots))
        self._ttl_ms = ttl_ms
        self._page_size = page_size
        self._skills: tuple[_Skill, ...] = ()
        self.skipped: tuple[str, ...] = ()
        self.refresh()

    @property
    def roots(self) -> tuple[Path, ...]:
        """Skill root directories, in scan order."""
        return self._roots

    @property
    def ttl_ms(self) -> int:
        return self._ttl_ms

    @property
    def skills(self) -> tuple[_Skill, ...]:
        """Validated skills, sorted by name."""
        return self._skills

    def refresh(self) -> None:
        """Re-scan every root and rebuild the snapshot."""
        by_name: dict[str, _Skill] = {}
        skipped: list[str] = []

        for root in self._roots:
            if not root.is_dir():
                logger.debug("Skills root does not exist: %s", root)
                continue

            for child in sorted(root.iterdir()):
                if not child.is_dir():
                    continue
                if child.name in by_name:
                    # Bundled roots are scanned first, so a same-named skill in
                    # a user-supplied root can never shadow a bundled one.
                    skipped.append(f"{child.name}: duplicate of a skill from an earlier root")
                    continue

                result = _load_skill(child)
                if isinstance(result, str):
                    skipped.append(result)
                    continue
                by_name[result.name] = result

        self._skills = tuple(by_name[name] for name in sorted(by_name))
        self.skipped = tuple(skipped)
        logger.info(
            "Skills catalog: %d skill(s) from %d root(s), %d skipped",
            len(self._skills),
            len(self._roots),
            len(self.skipped),
        )

    # -- Pagination ---------------------------------------------------------

    def list_page(self, cursor: str | None = None) -> tuple[list[SkillEntry], str | None]:
        """Return one page of skill entries plus the cursor for the next page.

        An entry is atomic, so the cursor never splits a skill's ``resources``.
        """
        start = 0
        if cursor:
            try:
                start = self._skills.index(self._skill_by_uri(_decode_cursor(cursor)))
            except (ValueError, binascii.Error, UnicodeDecodeError):
                raise MCPError(code=INVALID_PARAMS, message="Invalid cursor") from None
            start += 1

        page = self._skills[start : start + self._page_size]
        next_cursor = None
        if start + self._page_size < len(self._skills):
            next_cursor = _encode_cursor(page[-1].uri)
        return [skill.entry() for skill in page], next_cursor

    def get(self, uri: str) -> SkillEntry | None:
        """Look a skill up by URI, independently of any listing.

        ``uri`` is normally the ``SKILL.md`` URI. A URI pointing at any other
        file of a known skill (or at the skill root) resolves to that skill, so
        a host or user holding a supporting-file URI still gets the entry it
        needs to verify the read.
        """
        try:
            return self._skill_by_uri(uri).entry()
        except ValueError:
            pass

        parsed = urlsplit(uri)
        if parsed.scheme != "skill" or not parsed.netloc:
            return None
        # netloc is the first path segment: ``skill://<name>/<rest>``.
        name = unquote(parsed.netloc)
        for skill in self._skills:
            if skill.name == name:
                return skill.entry()
        return None

    def _skill_by_uri(self, uri: str) -> _Skill:
        for skill in self._skills:
            if skill.uri == uri:
                return skill
        raise ValueError(f"unknown skill URI: {uri}")


def _encode_cursor(uri: str) -> str:
    """Encode a pagination cursor. The token is opaque to clients."""
    return base64.urlsafe_b64encode(uri.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> str:
    """Decode a pagination cursor, tolerating stripped padding."""
    padding = "=" * (-len(cursor) % 4)
    return base64.urlsafe_b64decode(cursor + padding).decode("utf-8")


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------


class SkillFileResource(Resource):
    """One file of a skill, served exactly as it sits on disk.

    Text files are decoded without newline translation, so a skill authored
    with CRLF endings is served with CRLF — the bytes the manifest's ``size``
    and ``digest`` describe.
    """

    absolute_path: Path

    async def read(self) -> str | bytes:
        raw = self.absolute_path.read_bytes()
        if self.mime_type and self.mime_type.startswith("text/"):
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                # A text/* file that is not UTF-8 (latin-1, UTF-16, ...) has no
                # lossless text rendering, but the manifest already promises
                # these exact bytes. Serve them as a base64 blob instead of
                # failing the read and describing bytes nobody receives.
                logger.warning("Serving %s as a base64 blob: the file is not valid UTF-8", self.uri)
                return raw
        return raw


class SkillResourceProvider(Provider):
    """Serves the files of a single skill as ``skill://<name>/<path>`` resources.

    Every file in the skill's manifest becomes an individually addressable
    resource, so a host that resolves URIs from ``resources/list`` (rather than
    from a resource template) can read them directly.
    """

    def __init__(self, skill: _Skill) -> None:
        super().__init__()
        self._skill = skill

    @property
    def skill(self) -> _Skill:
        """The skill this provider serves."""
        return self._skill

    def _resource(self, entry: SkillFileEntry, path: Path) -> SkillFileResource:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return SkillFileResource(
            uri=AnyUrl(entry.uri),
            name=entry.uri.removeprefix("skill://"),
            description=f"{self._skill.name}: {path.name}",
            mime_type=mime_type,
            absolute_path=path,
        )

    async def _list_resources(self) -> Sequence[Resource]:
        return [self._resource(entry, path) for entry, path in zip(self._skill.files, self._skill.paths, strict=True)]

    async def _get_resource(self, uri: str, version: VersionSpec | None = None) -> Resource | None:
        path = self._skill.path_for(uri)
        if path is None:
            return None
        (entry,) = [candidate for candidate in self._skill.files if candidate.uri == uri]
        return self._resource(entry, path)

    def __repr__(self) -> str:
        return f"SkillResourceProvider(skill={self._skill.name!r}, files={len(self._skill.files)})"


# ---------------------------------------------------------------------------
# Extension
# ---------------------------------------------------------------------------


class SkillsExtension(ServerExtension):
    """SEP-2133 extension implementing ``skills/list`` and ``skills/get``.

    Registering this extension is what advertises
    ``capabilities.extensions["io.modelcontextprotocol/skills"]`` on the modern
    ``server/discover`` path. The legacy ``initialize`` response predates
    extensions and does not carry the field; that is expected, not a defect.
    """

    identifier = SKILLS_EXTENSION_ID

    def __init__(
        self,
        catalog: SkillCatalog,
        *,
        directory_read: bool = False,
    ) -> None:
        self._catalog = catalog
        self._directory_read = directory_read

    @property
    def catalog(self) -> SkillCatalog:
        """The catalog this extension serves."""
        return self._catalog

    def settings(self) -> dict[str, Any]:
        """Advertise the extension and whether ``resources/directory/read`` is served."""
        return {"directoryRead": self._directory_read}

    def methods(self) -> Sequence[MethodBinding]:
        return (
            MethodBinding(method="skills/list", params_type=SkillsListParams, handler=self._on_list),
            MethodBinding(method="skills/get", params_type=SkillsGetParams, handler=self._on_get),
        )

    async def _on_list(
        self,
        ctx: ServerRequestContext[Any, Any],  # noqa: ARG002 - unused, kept for the handler signature
        params: SkillsListParams,
    ) -> SkillsListResult:
        skills, next_cursor = self._catalog.list_page(params.cursor)
        return SkillsListResult(
            skills=skills,
            ttl_ms=self._catalog.ttl_ms,
            next_cursor=next_cursor,
        )

    async def _on_get(
        self,
        ctx: ServerRequestContext[Any, Any],  # noqa: ARG002 - unused, kept for the handler signature
        params: SkillsGetParams,
    ) -> SkillsGetResult:
        entry = self._catalog.get(params.uri)
        if entry is None:
            # SEP-2640: an unknown URI is -32602, the same code
            # ``resources/read`` uses for unknown resources.
            raise MCPError(code=INVALID_PARAMS, message=f"Unknown skill URI: {params.uri}")
        return SkillsGetResult(skill=entry, ttl_ms=self._catalog.ttl_ms)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def bundled_skills_dir() -> Path:
    """Directory of the skills shipped with this package."""
    return Path(__file__).parent / "data" / "skills"


def default_skill_roots() -> list[Path]:
    """Skill roots: the bundled directory first, then any configured extras.

    Extra roots come from ``SHOTGRID_MCP_SKILLS_DIR``, a
    ``os.pathsep``-separated list. Bundled skills are scanned first, so a
    same-named skill in a user root cannot shadow one of ours.
    """
    roots: list[Path] = [bundled_skills_dir()]
    for raw in os.environ.get(ENV_SKILLS_DIRS, "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()).expanduser())
    return roots


def register_skills(
    server: FastMCPType,
    *,
    roots: Sequence[Path | str] | Path | str | None = None,
    ttl_ms: int = DEFAULT_TTL_MS,
    page_size: int = DEFAULT_PAGE_SIZE,
    directory_read: bool = False,
) -> SkillsExtension:
    """Expose skills on a FastMCP server and install the Skills extension.

    Each validated skill directory is added as its own
    :class:`SkillResourceProvider`, so the resources the server answers for are
    exactly the skills the extension lists — a directory that failed validation
    (missing frontmatter, a ``name`` that does not match its directory) is never
    half-served.

    Args:
        server: FastMCP server to register on.
        roots: Skill root directories. Defaults to :func:`default_skill_roots`.
        ttl_ms: Freshness hint returned with list/get results.
        page_size: Skills returned per ``skills/list`` page.
        directory_read: Advertise ``directoryRead``. Only set this when the
            server also implements ``resources/directory/read``.

    Returns:
        SkillsExtension: the registered extension.
    """
    catalog = SkillCatalog(roots if roots is not None else default_skill_roots(), ttl_ms=ttl_ms, page_size=page_size)

    for skill in catalog.skills:
        server.add_provider(SkillResourceProvider(skill))

    extension = SkillsExtension(catalog, directory_read=directory_read)
    # ``FastMCP(extensions=[...])`` is not supported on fastmcp 4.0.5; the
    # instance method is the supported path.
    server.add_extension(extension)
    logger.info("Registered %s extension with %d skill(s)", SKILLS_EXTENSION_ID, len(catalog.skills))
    return extension
