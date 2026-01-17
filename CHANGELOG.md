## v0.15.3 (2026-01-17)

### Fix

- use vx uvx in justfile instead of bare uvx

## v0.15.2 (2026-01-17)

### Fix

- **docs**: regenerate package-lock.json for npm ci compatibility
- **ci**: add pull-requests write permission for PR comments

## v0.15.1 (2026-01-04)

### Fix

- **ci**: add --system flag to vx uv pip install for CI environment

## v0.15.0 (2025-12-29)

### Feat

- simplify JSON Schema for LLM API compatibility and migrate CI to vx

## v0.14.1 (2025-12-25)

### Fix

- normalize integer entity IDs to dict format in API tools

## v0.14.0 (2025-12-03)

### Feat

- add sg_url to all entity creation responses

## v0.13.4 (2025-12-01)

### Fix

- **cloud**: use HTTP ASGI app for FastMCP Cloud multi-site support

## v0.13.3 (2025-12-01)

### Fix

- **ci**: use Python 3.12, add FastMCP Cloud support with dedicated entry point

## v0.13.2 (2025-12-01)

### Fix

- return structured results for API tools instead of primitives

## v0.13.1 (2025-11-28)

### Fix

- replace deprecated class-based Config with ConfigDict for Pydantic V2 compatibility

## v0.13.0 (2025-11-23)

### Feat

- improve MCP tool documentation and add missing ShotGrid API coverage
- add text_search minimum length validation and improve filter docs
- add user-friendly API improvements and comprehensive tests
- add automatic datetime format normalization for filters
- implement MockgunExt.update method and improve test coverage
- migrate from diskcache to diskcache_rs for improved performance

### Fix

- resolve test failures in search tools
- update dependencies to resolve security vulnerabilities
- only pass page parameter to sg.find when it has a value
- unify ruff version and fix import sorting
- normalize line endings to LF for Python files
- add __all__ to models.py to re-export TimeFilter
- add shotgrid-query to requirements-dev.txt
- reduce complexity of register_create_tools and fix TimeFilter import
- simplify filter validation and fix return type mismatches

### Refactor

- reduce complexity of register_advanced_search_tool
- organize schema cache directory alongside logs

## v0.12.0 (2025-11-19)

### Feat

- add standalone ASGI application support for cloud deployment

### Fix

- remove module-level server initialization to prevent HTTP mode startup errors
- implement lazy initialization for ASGI to prevent Docker build errors

## v0.11.0 (2025-11-19)

### Feat

- refactor CLI to use subcommands and implement per-request credentials
- add stdio and streamable HTTP transport support with click CLI

### Fix

- resolve lint and test failures

## v0.10.2 (2025-11-19)

### Fix

- remove test code and add trailing newline in logger.py
- correct playlist detail URL format from /Playlist/detail/ to /detail/Playlist/

## v0.10.1 (2025-11-16)

### Fix

- ensure PyPI wheel is valid for upload

## v0.10.0 (2025-11-16)

### Feat

- improve advanced search filters and local tooling

## v0.9.0 (2025-11-15)

### Feat

- add schema resources and playlist URL variants

## v0.8.1 (2025-05-29)

### Fix

- **deps**: update dependency mintlify to v4.0.560

## v0.8.0 (2025-04-28)

### Feat

- optimize thumbnail download functionality

### Fix

- Fix B904 warnings in api_client.py
- Fix lint issues in utils and thumbnail tools
- Fix MockgunExt to support page parameter and fix tests
- handle string attachment data in thumbnail download
- simplify thumbnail download implementation to fix URL handling issue
- correct thumbnail download method to use proper ShotGrid API parameters
- correct YAML syntax in codecov workflow
- correct thumbnail URL retrieval method

### Refactor

- Remove compatibility code and simplify connection pool
- Use _download_with_shotgun_api for thumbnail downloads
- Simplify thumbnail download code
- Remove ShotgunConfig class and use custom_types.py
- Use get_shotgun_connection_args in create_shotgun_connection
- Use get_shotgun_connection_args in instanceFactory
- move generate_default_file_path to utils.py for better maintainability

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
