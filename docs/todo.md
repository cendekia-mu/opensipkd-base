Identifying Security Issues

Initiating System Assessment

Defining Project's Scope

Analyzing Python Dependency

Project Evaluation: opensipkd-base
──────

1. Executive Summary & Project Profile
| Attribute                  | Details                                                                                               |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| Package Name               | opensipkd_base (Version 5.0.4) Current Branch                                                         |
| oracle.apps Target Purpose | Core base framework and shared foundation library for openSIPKD applications (Indonesian              |
|                            | regional government municipal ERPs, e-Tax, PBB, BPHTB, Samsat, etc.) Core Tech Stack                  |
|                            | Python (>= 3.8), Pyramid WSGI, SQLAlchemy, Ziggurat Foundations (RBAC/Auth), Deform &                 |
|                            | Colander (Form schema & widgets), Chameleon / ZPT (Templating), Waitress, Alembic Databases Supported |
|                            | PostgreSQL (default) and Oracle DB (oracledb, instantclient)                                          |
| ──────                     |

2. Architecture & Key Strengths

* Declarative Route & Menu Engine:

• Routes and dynamic menu trees are configured declaratively via CSV/XLSX files using __init__.py:734-751, automating permissions, views, and navigation hierarchies.

* Robust RBAC & Security Integration:
• Integration with users.py provides a flexible RBAC model (Users, Groups, Permissions, and Resource-level ACLs). • Custom authentication policy in security.py:59-118 supports both cookie-based auth (with configurable samesite, http_only, and secure flags) and RPC HMAC signature verification. • Single-device session locking mechanism in __init__.py:534-546.

Multi-Database Support (PostgreSQL + Oracle):
• Dynamic schema scoping via os.environ.get("PUBLIC_SCHEMA") in base.py:28-31. • Custom SQLAlchemy type decorators such as users.py:32-52 and Oracle connection output handlers for timezone handling.

Standard CRUD Model Hierarchy:

• Inheritance chain (CommonModel → DefaultModel → StandarModel → KodeModel / NamaModel / UraianModel) provides consistent timestamps (created, updated), user tracking (create_uid, update_uid), status flags, and helper queries.

──────

1. Critical Findings & Security Assessment

│ Warning │ 1. Hardcoded Secrets and Credentials in Configuration Files │ In development.ini:78-88, sensitive credentials (including Oracle database connection strings, BSRE e-sign tokens, │ and SMTP passwords) are stored in plaintext. │ Recommendation: Move all credentials to environment variables or an untracked .env / local.ini file.

│ Caution │ 2. Authentication Bypass in Debug Mode for RPC API │ In api.py:28-30: │ │ # bypass cek authentication for development │ if http_userid == 'admin' and log.parent.level == logging.DEBUG: │ return user │ │ If DEBUG logging is enabled (common during staging or troubleshooting), any incoming RPC request with HTTP_USERID: │ admin skips HMAC signature verification entirely.

│ Important │ 3. Overly Permissive Global CORS Headers │ In __init__.py:492-532, add_cors_headers_response_callback globally attaches: │ │ 'Access-Control-Allow-Origin': '' │ 'Access-Control-Allow-Methods': '' │ 'Access-Control-Allow-Headers': '*' │ │ This applies to every response, allowing any external origin to interact with the API without restriction. │ │ 4. Global CSRF Protection Disabled by Default │ In __init__.py:224-226, config.set_default_csrf_options(require_csrf=False) disables Pyramid's global CSRF │ protection across all views by default. ──────

1. Code Quality, Modernization & Technical Debt
Python 3.12+ / 3.13 Compatibility Risks:
• cgi.FieldStorage: Imported in base_views.py:5. The cgi standard library module was deprecated in 3.11 and completely removed in Python 3.13 (PEP 594). • pkg_resources: Used in __init__.py:18 (resource_filename). This is deprecated; use standard library importlib.resources.

Monolithic Files:
• base_views.py is 1,647 lines (62 KB). • __init__.py is 893 lines (33 KB). • user_login.py is 838 lines (33 KB). • High cyclomatic complexity makes maintenance and isolated testing difficult.

Broad Exception Handling:
• Several bare try ... except: blocks exist (e.g., __init__.py:389-390 for Oracle client init), which suppress real errors like driver mismatches or missing environment variables.

Coupling Base Framework with Module Implementations:
• opensipkd_base contains direct references and configuration fallbacks for specific downstream modules (like PBB, BSRE, Samsat) inside development.ini:81-89 and initializedb.py.

──────

5. Testing, QA & CI/CD Status
• Test Suite: No automated test suite is configured in the root or in pyproject.toml. Old legacy test files exist in tests (ipr_test.py, test_functional_base.py, test_view_base.py), but they are unmaintained and not run. • CI/CD Pipelines: No automated pipeline (.github/workflows/ or .gitlab-ci.yml) is present for testing, linting (flake8/ruff), type checking (mypy), or build validation. ──────

6. Repository Hygiene & Packaging

Artifact Cleanliness:

• The repository contains legacy backups in bak/ containing executable binaries (lpr.exe), .whl files (Shapely-1.6.4.post1-cp27-cp27m-win_amd64.whl), and old builds (build/, tmp/, log_file/, 2025/). • These should be removed from git tracking and added to .gitignore.

pyproject.toml Dependency Specifications:
• In pyproject.toml:21-48, dependencies are unpinned (no minimum/maximum versions for critical packages like pyramid, sqlalchemy, deform). • Includes redundant entries like "asyncio" (standard library module in Python 3.4+).

1. Strategic Recommendations & Action Plan

flowchart LR A["1. Security Hardening"] --> B["2. Modernization & Cleanup"] B --> C["3. Testing & CI/CD"] C --> D["4. Modular Refactoring"]

| Priority | Task                  | Action Details                                                                            |
| -------- | --------------------- | ----------------------------------------------------------------------------------------- |
| High     | Secrets Management    | Move database passwords and API tokens out of development.ini into                        |  | environment variables or untracked local config. High | Remove Debug Auth Bypass | Remove http_userid == 'admin' signature bypass in api.py. High | Python 3.13 Compatibility | Replace cgi.FieldStorage in base_views.py:5 and migrate pkg_resources in |  | __init__.py:18 to importlib.resources. |
| Medium   | Repository Cleanup    | Purge bak/, build/, tmp/, and .whl/.exe binaries from git tracking and update .gitignore. |
| Medium   | Setup Test Suite & CI | Move and modernize tests into a standard tests/ directory with pytest and                 |  | webtest, and establish a basic CI workflow.           |
| Low      | Modularize Views      | Split base_views.py into smaller, focused modules (e.g. crud.py,                          |  | export.py, grid.py).                                  |