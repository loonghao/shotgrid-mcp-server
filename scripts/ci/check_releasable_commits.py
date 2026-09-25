#!/usr/bin/env python3
"""Decide whether a commit window contains something worth releasing.

The release workflow uses this to keep release-please from cutting a release
for commits that do not move the product. release-please's own rule is blunt:
in ``determineReleaseType`` anything that is neither breaking nor a ``feat``
falls through to a patch bump, so a ``docs:`` or ``chore:`` commit alone is
enough to produce a release. That matters here because any automation that
regenerates files on ``main`` would otherwise keep the release PR alive.

The gate deliberately fails open: if the git range cannot be resolved the
script reports ``releasable=true`` so a release is never silently suppressed.
"""

# Import built-in modules
import argparse
import re
import subprocess
import sys
from pathlib import Path

# Only these conventional-commit types are treated as release-worthy. A
# ``BREAKING CHANGE:`` footer counts too, whatever the type of the commit.
RELEASABLE_PATTERN = re.compile(
    r"^(feat|fix|perf|refactor|revert)(\([^)]*\))?!?:|^BREAKING CHANGE:",
    re.MULTILINE,
)

TAG_PATTERN = "v*"


def is_releasable(commit_text):
    """Return True when a commit window contains at least one release-worthy commit.

    ``commit_text`` is the concatenated ``%s%n%b`` (subject plus body) of every
    commit in the window.
    """
    return bool(RELEASABLE_PATTERN.search(commit_text or ""))


def last_release_tag(cwd=None):
    """Return the most recent ``v*`` tag reachable from HEAD, or None."""
    result = subprocess.run(
        ["git", "describe", "--tags", "--match", TAG_PATTERN, "--abbrev=0"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commit_window(range_spec, cwd=None):
    """Return the combined subjects and bodies of the commits in a git range."""
    result = subprocess.run(
        ["git", "log", "--no-merges", "--format=%s%n%b", range_spec],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git log failed for range {range_spec!r}: {result.stderr.strip()}")
    return result.stdout


def resolve_range(cwd=None):
    """Return a git range covering everything since the last ``v*`` tag."""
    tag = last_release_tag(cwd=cwd)
    return f"{tag}..HEAD" if tag else "HEAD"


def decide(range_spec=None, cwd=None):
    """Return True when the window should be released.

    With no explicit range the window is everything since the last ``v*`` tag,
    or the whole history when the repo has no such tag yet.
    """
    return is_releasable(commit_window(range_spec or resolve_range(cwd=cwd), cwd=cwd))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--range", help="git range to inspect; defaults to last v* tag..HEAD")
    parser.add_argument("--cwd", help="repository to inspect; defaults to the current directory")
    parser.add_argument(
        "--github-output",
        help="append 'releasable=<bool>' to this file, as GitHub Actions expects",
    )
    args = parser.parse_args(argv)

    try:
        releasable = decide(range_spec=args.range, cwd=args.cwd)
    except Exception as error:  # noqa: BLE001 - fail open, but say why
        print(f"::error::{error}")
        print("Failing open: treating the window as releasable")
        releasable = True

    line = f"releasable={str(releasable).lower()}"
    print(line)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
