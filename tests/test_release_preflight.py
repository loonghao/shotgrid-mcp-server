"""Regression tests for the release workflow's release-gate scripts.

Both scripts encode non-trivial rules that a future edit could silently break:
which commits are allowed to trigger a release, and which artifacts belong to
the version being published. The scripts live under ``scripts/ci`` rather than
in the package, so they are imported from disk by path.
"""

# Import built-in modules
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

# Import third-party modules
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "ci"


def _load(module_name, filename):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_releasable = _load("check_releasable_commits", "check_releasable_commits.py")
verify_release_dist = _load("verify_release_dist", "verify_release_dist.py")


class TestIsReleasable:
    """The release gate: which commit windows may cut a release."""

    @pytest.mark.parametrize(
        "message",
        [
            "feat: add a dashboard",
            "feat(skills): expose Agent Skills over MCP",
            "fix: handle non-UTF-8 files",
            "fix(skills): accept frontmatter at EOF (#166)",
            "perf(cache): reuse the client",
            "refactor: split the module",
            "revert: feat: add a dashboard",
            "feat!: drop python 3.10",
            "fix(api)!: rename a field",
        ],
    )
    def test_releasable_types_open_the_gate(self, message):
        assert check_releasable.is_releasable(message) is True

    @pytest.mark.parametrize(
        "message",
        [
            "docs(skills): pin the blob mimeType ruling",
            "ci: run the wire-level check",
            "chore(main): release 0.17.2",
            "chore(deps): update fastmcp to 4.1.0",
            "style: format the module",
            "build: bump hatchling",
            "test: add coverage",
            "bump: version 0.17.0 -> 0.17.1",
        ],
    )
    def test_release_neutral_types_do_not_open_the_gate(self, message):
        assert check_releasable.is_releasable(message) is False

    def test_breaking_change_footer_opens_the_gate(self):
        message = "refactor: rename the setting\n\nBREAKING CHANGE: the old name is gone"
        assert check_releasable.is_releasable(message) is True

    def test_breaking_change_mention_in_a_subject_does_not(self):
        # Only a footer counts; prose about breaking changes must not release.
        assert check_releasable.is_releasable("docs: mention BREAKING CHANGE in the guide") is False

    def test_empty_window_closes_the_gate(self):
        assert check_releasable.is_releasable("") is False

    def test_one_releasable_commit_among_neutral_ones(self):
        window = "docs: update the guide\nchore: tidy\nfix: correct the parser\nci: tweak\n"
        assert check_releasable.is_releasable(window) is True

    def test_body_only_breaking_change_is_found(self):
        # The body is scanned too, so a breaking footer on a neutral type counts.
        window = "chore: bump a dependency\nBREAKING CHANGE: dropped python 3.10\n"
        assert check_releasable.is_releasable(window) is True


class TestReleaseWindowGit:
    """The git plumbing behind the gate."""

    @staticmethod
    def _git(repo, *args):
        # Inherit the real environment: git needs PATH to find its own helpers
        # and, on Windows, SYSTEMROOT as well. Only the commit identity is
        # overridden, so the fixtures do not depend on the caller's git config.
        subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            env={
                **os.environ,
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
            },
        )

    @classmethod
    def _commit(cls, repo, message):
        (repo / "file.txt").write_text(message, encoding="utf-8")
        cls._git(repo, "add", "file.txt")
        cls._git(repo, "commit", "-m", message)

    @pytest.fixture()
    def repo(self, tmp_path):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            pytest.skip("git is not available")
        repo = tmp_path / "repo"
        repo.mkdir()
        self._git(repo, "init", "-q", "-b", "main")
        return repo

    def test_window_covers_only_commits_since_the_last_tag(self, repo):
        self._commit(repo, "feat: first")
        self._git(repo, "tag", "v0.1.0")
        self._commit(repo, "docs: only documentation after the tag")

        assert check_releasable.resolve_range(cwd=repo) == "v0.1.0..HEAD"
        assert check_releasable.decide(cwd=repo) is False

        self._commit(repo, "fix: a real fix")
        assert check_releasable.decide(cwd=repo) is True

    def test_whole_history_is_scanned_without_a_tag(self, repo):
        self._commit(repo, "feat: first")
        assert check_releasable.last_release_tag(cwd=repo) is None
        assert check_releasable.resolve_range(cwd=repo) == "HEAD"
        assert check_releasable.decide(cwd=repo) is True

    def test_cli_reports_through_the_github_output_file(self, repo, tmp_path):
        self._commit(repo, "feat: first")
        self._commit(repo, "chore: nothing releasable")
        output = tmp_path / "github_output"

        exit_code = check_releasable.main(["--cwd", str(repo), "--github-output", str(output)])

        assert exit_code == 0
        assert output.read_text(encoding="utf-8") == "releasable=true\n"

    def test_cli_fails_open_on_an_unknown_range(self, repo, tmp_path):
        output = tmp_path / "github_output"

        exit_code = check_releasable.main(
            ["--range", "no-such-range..HEAD", "--cwd", str(repo), "--github-output", str(output)]
        )

        # A broken range must never silently suppress a release.
        assert exit_code == 0
        assert output.read_text(encoding="utf-8") == "releasable=true\n"


class TestReleaseDist:
    """The artifact guard in front of the immutable PyPI upload."""

    @pytest.mark.parametrize(
        "name",
        [
            "shotgrid_mcp_server-0.17.2-py3-none-any.whl",
            "shotgrid_mcp_server-0.17.2.tar.gz",
        ],
    )
    def test_matching_artifacts_pass(self, name):
        assert verify_release_dist.mismatched_artifacts("0.17.2", [name]) == []

    @pytest.mark.parametrize(
        "name",
        [
            # A bare prefix would wrongly accept this one.
            "shotgrid_mcp_server-0.17.20-py3-none-any.whl",
            "shotgrid_mcp_server-0.17.1-py3-none-any.whl",
            "shotgrid_mcp_server-0.17.1.tar.gz",
            "unrelated-0.17.2-py3-none-any.whl",
        ],
    )
    def test_foreign_artifacts_are_rejected(self, name):
        assert verify_release_dist.mismatched_artifacts("0.17.2", [name]) == [name]

    def test_no_version_skips_the_check(self):
        assert verify_release_dist.mismatched_artifacts("", ["anything-1.0.0.whl"]) == []

    def test_resolve_version_prefers_the_tag_for_a_backfill(self):
        assert verify_release_dist.resolve_version("workflow_dispatch", "v0.17.2", "0.18.0") == "0.17.2"

    def test_resolve_version_uses_the_release_version_otherwise(self):
        assert verify_release_dist.resolve_version("push", "v0.17.2", "0.18.0") == "0.18.0"

    def test_resolve_version_strips_a_leading_v(self):
        assert verify_release_dist.resolve_version("workflow_dispatch", "V0.17.2", "") == "0.17.2"

    def test_main_fails_on_a_mismatched_dist(self, tmp_path):
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "shotgrid_mcp_server-0.17.1-py3-none-any.whl").write_text("", encoding="utf-8")

        exit_code = verify_release_dist.main(["--dist-dir", str(dist), "--version", "0.17.2", "--event-name", "push"])

        assert exit_code == 1

    def test_main_passes_on_a_matching_dist(self, tmp_path):
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "shotgrid_mcp_server-0.17.2-py3-none-any.whl").write_text("", encoding="utf-8")
        (dist / "shotgrid_mcp_server-0.17.2.tar.gz").write_text("", encoding="utf-8")

        exit_code = verify_release_dist.main(["--dist-dir", str(dist), "--version", "0.17.2", "--event-name", "push"])

        assert exit_code == 0

    def test_main_skips_without_a_version(self, tmp_path):
        dist = tmp_path / "dist"
        dist.mkdir()
        assert verify_release_dist.main(["--dist-dir", str(dist)]) == 0


def test_scripts_run_under_the_runner_python():
    for script in ("check_releasable_commits.py", "verify_release_dist.py"):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
