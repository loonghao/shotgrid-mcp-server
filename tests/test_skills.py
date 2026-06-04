"""Tests for skill package structure and importability."""

# Import built-in modules
import sys
from pathlib import Path

import pytest
import yaml

# Base path
SKILLS_DIR = Path(__file__).parent.parent / "skills"
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

EXPECTED_SKILLS = [
    "shotgrid-crud",
    "shotgrid-search",
    "shotgrid-batch",
    "shotgrid-media",
    "shotgrid-notes",
    "shotgrid-playlists",
    "shotgrid-api",
    "shotgrid-vendor",
]


class TestSkillStructure:
    """Verify each skill package has the required structure."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_dir_exists(self, skill_name):
        """Skill directory exists."""
        assert (SKILLS_DIR / skill_name).is_dir()

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_skill_md(self, skill_name):
        """SKILL.md exists with valid frontmatter."""
        md_path = SKILLS_DIR / skill_name / "SKILL.md"
        assert md_path.is_file()
        content = md_path.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "name:" in content
        assert "dcc-mcp:" in content or "metadata:" in content

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_tools_yaml(self, skill_name):
        """tools.yaml exists and is valid."""
        yaml_path = SKILLS_DIR / skill_name / "tools.yaml"
        assert yaml_path.is_file()
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert "tools" in data
        assert len(data["tools"]) > 0

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_groups_yaml(self, skill_name):
        """groups.yaml exists and is valid."""
        yaml_path = SKILLS_DIR / skill_name / "groups.yaml"
        assert yaml_path.is_file()
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert "groups" in data

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_scripts_dir(self, skill_name):
        """scripts/ directory exists with Python files."""
        scripts_dir = SKILLS_DIR / skill_name / "scripts"
        assert scripts_dir.is_dir()
        py_files = list(scripts_dir.glob("*.py"))
        assert len(py_files) > 0


class TestToolDefinitions:
    """Verify each tool has required fields."""

    REQUIRED_FIELDS = ["source_file", "execution", "affinity", "read_only"]

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_tools_have_required_fields(self, skill_name):
        """Every tool in tools.yaml has source_file, execution, affinity, read_only."""
        yaml_path = SKILLS_DIR / skill_name / "tools.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        for tool in data["tools"]:
            for field in self.REQUIRED_FIELDS:
                assert field in tool, f"Tool '{tool['name']}' in {skill_name} missing field: {field}"

            # source_file must point to a script in scripts/
            source = tool["source_file"]
            assert source.startswith("scripts/"), f"source_file must start with 'scripts/': {source}"
            script_path = SKILLS_DIR / skill_name / source
            assert script_path.is_file(), f"Script not found: {script_path}"

            # affinity must be "any" for ShotGrid (no GUI host)
            assert tool["affinity"] == "any", f"Tool '{tool['name']}' affinity must be 'any', got {tool['affinity']}"

            # execution must be "sync"
            assert tool["execution"] == "sync", f"Tool '{tool['name']}' execution must be 'sync'"


class TestScriptImportability:
    """Verify skill scripts can be imported."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_scripts_use_skill_decorator(self, skill_name):
        """All scripts use @skill_entry and run_main."""
        scripts_dir = SKILLS_DIR / skill_name / "scripts"
        for script in scripts_dir.glob("*.py"):
            content = script.read_text(encoding="utf-8")
            assert "skill_entry" in content, f"{script.name} missing @skill_entry"
            assert "run_main" in content, f"{script.name} missing run_main"


class TestSkillCounts:
    """Verify expected tool counts per skill."""

    EXPECTED_COUNTS = {
        "shotgrid-crud": 5,
        "shotgrid-search": 7,
        "shotgrid-batch": 3,
        "shotgrid-media": 3,
        "shotgrid-notes": 3,
        "shotgrid-playlists": 4,
        "shotgrid-api": 13,
        "shotgrid-vendor": 3,
    }

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_expected_tool_count(self, skill_name):
        """Each skill has the expected number of tools."""
        yaml_path = SKILLS_DIR / skill_name / "tools.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        expected = self.EXPECTED_COUNTS.get(skill_name)
        assert len(data["tools"]) == expected, (
            f"{skill_name}: expected {expected} tools, got {len(data['tools'])}"
        )

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_scripts_match_tools(self, skill_name):
        """Number of scripts matches number of tools."""
        yaml_path = SKILLS_DIR / skill_name / "tools.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        scripts_dir = SKILLS_DIR / skill_name / "scripts"
        py_files = list(scripts_dir.glob("*.py"))
        assert len(py_files) == len(data["tools"]), (
            f"{skill_name}: {len(py_files)} scripts vs {len(data['tools'])} tools"
        )
