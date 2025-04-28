## v0.7.7 (2025-04-28)

### Fix

- **deps**: update dependency mintlify to v4.0.510

## v0.7.6 (2025-04-25)

### Fix

- **deps**: update dependency mintlify to v4.0.507

## v0.7.5 (2025-04-23)

### Fix

- update tool names to comply with MCP naming convention

### Refactor

- standardize tool naming convention

## v0.7.4 (2025-04-23)

### Fix

- **deps**: update dependency mintlify to v4.0.504

## v0.7.3 (2025-04-23)

### Fix

- add missing sg parameter to download_thumbnail call
- make thumbnail tests work in both test_server.py and test_thumbnail_tools.py
- fix pyproject.toml format issues

## v0.7.2 (2025-04-23)

### Fix

- specify Python 3.10 for uvx to ensure compatibility

## v0.7.1 (2025-04-22)

### Fix

- **deps**: update dependency mintlify to v4.0.497

## v0.7.0 (2025-04-21)

### Feat

- add note and playlist tools
- add direct ShotGrid API tools for increased flexibility
- add standardized response models and fix circular dependencies
- enhance playlist creation to include URL in response
- enhance note and playlist functionality with vendor support

### Fix

- fix test failures and lint issues
- update mockgun_ext to handle dict order items and update test_find_recent_playlists to be more flexible
- update mockgun_ext to handle dict values in sort and update test_find_recent_playlists to use a more recent date
- update mockgun_ext to handle non-string order fields and update tests to handle TextContent responses
- update playlist_tools to handle Mockgun limitations and use TimeUnit enum
- update error_handler to handle entity not found errors correctly
- resolve test failures in error_handler and api_tools tests
- correct parameter format in note tools tests
- parse JSON responses in vendor tools
- update playlist URL format to match ShotGrid web interface

### Refactor

- update thumbnail_tools.py to use new return value format
- update search_tools.py to use new return value format

## v0.6.0 (2025-04-16)

### Feat

- implement PRD v2 improvements for date handling and error messages

## v0.5.0 (2025-04-16)

### Feat

- improve error messages for missing environment variables

## v0.4.0 (2025-04-16)

### Feat

- add static site generation for offline documentation hosting
- enhance filter processing and add data type utilities

### Fix

- update documentation workflow for Mintlify CLI changes
- update documentation workflow for Mintlify CLI changes
- simplify API documentation generation to static files
- fix indentation in temporary script for API documentation
- use temporary script for API documentation generation
- simplify API documentation generation
- update Sphinx configuration to support both .rst and .md files
- improve Sphinx API documentation generation
- add Sphinx configuration for API documentation
- update mintlify commands to use npx

### Refactor

- reduce code complexity to fix lint issues
- encapsulate documentation generation in nox commands
- use Pydantic models for filter handling
- use Pydantic models for data validation and serialization

## v0.3.5 (2025-04-16)

### Fix

- **deps**: update dependency mintlify to v4

## v0.3.4 (2025-04-15)

### Fix

- use uvx nox -s build-wheel for package building

## v0.3.3 (2025-04-15)

### Fix

- use uvx for all commands to avoid pip module issues
- use Python built-in venv module instead of uv venv

## v0.3.2 (2025-04-15)

### Fix

- handle direct git dependencies for PyPI publishing
- ensure virtual environment is activated in all workflow steps

## v0.3.1 (2025-04-15)

### Refactor

- **workflows**: Update dependency installation in workflows

## v0.3.0 (2025-04-15)

### Feat

- add Mintlify docs deployment workflow
- update PyPI publishing workflow to improve build and release process\

### Fix

- standardize uv usage in CI workflow to use uvx for nox execution

## v0.2.6 (2025-04-15)

### Fix

- resolve ruff linting issues with unused imports
- resolve type checking issues and update tests
- resolve ruff linting issues with imports

## v0.2.5 (2025-01-05)

### Refactor

- **server**: Refactor imports and add serialization method for entities
- **server**: Update environment variable names and logging for ShotGrid connection pool

## v0.2.4 (2025-01-05)

### Refactor

- **deps**: Update shotgun-api3 dependency and add uvx tool configuration

## v0.2.3 (2025-01-05)

### Refactor

- **deps**: Update dependencies and lock file

## v0.2.2 (2025-01-05)

### Refactor

- **server**: Refactor import statements in connection_pool and add test_imports script

## v0.2.1 (2025-01-05)

### Refactor

- **workflows**: Update dependency installation in workflows

## v0.2.0 (2025-01-05)

### Feat

- Implement ShotGrid client factories and enhance connection pool

### Refactor

- **server**: Refactor server tools registration and error handling

## v0.1.0 (2025-01-05)

### Feat

- Initialize ShotGrid MCP Server project structure and dependencies Add initial files and directories for the ShotGrid MCP Server project, including examples, src, tests, and documentation.
