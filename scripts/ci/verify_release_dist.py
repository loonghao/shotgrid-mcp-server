#!/usr/bin/env python3
"""Assert that the artifacts in dist/ belong to the version being released.

PyPI filenames are immutable: a version that was uploaded once can never be
overwritten or deleted. Publishing artifacts built from the wrong revision
would therefore burn that version number permanently, so the release workflow
checks the filenames against the version before handing them to PyPI.
"""

# Import built-in modules
import argparse
import sys
from pathlib import Path

PACKAGE_PREFIX = "shotgrid_mcp_server"


def resolve_version(event_name, tag_name, release_version):
    """Return the version the release is about to publish.

    A manual backfill builds the requested tag, so the tag wins there; a
    release-please run publishes whatever version it just created.
    """
    if (event_name or "").strip() == "workflow_dispatch":
        return (tag_name or "").strip().lstrip("vV")
    return (release_version or "").strip()


def mismatched_artifacts(version, names):
    """Return the artifact names that do not belong to ``version``."""
    if not version:
        return []
    # Anchor on the separator that follows the version: a bare prefix would let
    # "0.17.2" accept "shotgrid_mcp_server-0.17.20-py3-none-any.whl".
    expected = (f"{PACKAGE_PREFIX}-{version}-", f"{PACKAGE_PREFIX}-{version}.tar.gz")
    return [name for name in names if not name.startswith(expected)]


def artifact_names(dist_dir):
    """Return the wheel and sdist filenames in ``dist_dir``."""
    root = Path(dist_dir)
    return sorted(p.name for p in root.glob("*.whl")) + sorted(p.name for p in root.glob("*.tar.gz"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist", help="directory holding the built artifacts")
    parser.add_argument("--version", default="", help="release-please version, e.g. 0.17.2")
    parser.add_argument("--tag-name", default="", help="workflow_dispatch tag input, e.g. v0.17.2")
    parser.add_argument("--event-name", default="", help="GitHub event that started the run")
    args = parser.parse_args(argv)

    version = resolve_version(args.event_name, args.tag_name, args.version)
    if not version:
        print("No release version resolved; skipping the tag/artifact check")
        return 0

    names = artifact_names(args.dist_dir)
    mismatched = mismatched_artifacts(version, names)
    if mismatched:
        print(f"::error::dist artifacts do not match version {version}: {', '.join(mismatched)}")
        return 1

    print(f"OK: {len(names)} artifact(s) match version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
