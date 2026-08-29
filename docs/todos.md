# Project Evaluation & TODOs: `opensipkd_base`

---

## 1. Project Overview & Profile

| Attribute | Details |
| :--- | :--- |
| **Package Name** | `opensipkd_base` (Version `5.0.4`) |
| **Current Branch** | `oracle.apps` |
| **Target Purpose** | Core base framework and shared foundation library for openSIPKD applications (Indonesian regional government municipal ERPs, e-Tax, PBB, BPHTB, Samsat, etc.) |
| **Core Tech Stack** | **Python** (>= 3.8), **Pyramid WSGI**, **SQLAlchemy**, **Ziggurat Foundations** (RBAC/Auth), **Deform & Colander** (Form schema & widgets), **Chameleon / ZPT** (Templating), **Waitress**, **Alembic** |
| **Databases Supported** | **PostgreSQL** (default) and **Oracle DB** (`oracledb`, `instantclient`) |

---

## 2. Architecture & Key Strengths

1. **Declarative Route & Menu Engine**:
   - Routes and dynamic navigation trees are configured declaratively via CSV/XLSX files using [`BaseApp.route_from_csv`](../opensipkd/base/__init__.py), automating permissions, views, and navigation hierarchies.
2. **Robust RBAC & Security Integration**:
   - Integration with [Ziggurat Foundations](../opensipkd/base/models/users.py) provides a flexible RBAC model (Users, Groups, Permissions, and Resource-level ACLs).
   - Custom authentication policy in [`MySecurityPolicy`](../opensipkd/base/security.py) supports cookie-based auth (with configurable `samesite`, `http_only`, and `secure` flags) and RPC HMAC signature verification.
   - Single-device session locking mechanism in [`check_single_device_session`](../opensipkd/base/__init__.py).
3. **Multi-Database Support (PostgreSQL + Oracle)**:
   - Dynamic schema scoping via `os.environ.get("PUBLIC_SCHEMA")` in [`opensipkd/base/models/base.py`](../opensipkd/base/models/base.py).
   - Custom SQLAlchemy type decorators such as [`ForceUTCDatetime`](../opensipkd/base/models/users.py) and Oracle connection output handlers for timezone handling.
4. **Standard CRUD Model Hierarchy**:
   - Inheritance chain (`CommonModel` $\rightarrow$ `DefaultModel` $\rightarrow$ `StandarModel` $\rightarrow$ `KodeModel` / `NamaModel` / `UraianModel`) provides consistent timestamps (`created`, `updated`), user tracking (`create_uid`, `update_uid`), status flags, and helper queries.

---

## 3. Critical Findings & Security Assessment

### 1. Hardcoded Secrets and Plaintext Credentials
- **Issue**: In [`development.ini`](../development.ini), sensitive credentials (including Oracle database connection strings, BSRE e-sign tokens, and SMTP passwords) are stored in plaintext.
- **Risk**: Exposure of administrative database credentials and third-party signing keys.
- **Action**: Extract all credentials into environment variables or untracked `.env` / `live.ini` files.

### 2. Authentication Bypass in Debug Mode for RPC API
- **Issue**: In [`opensipkd/base/tools/api.py`](../opensipkd/base/tools/api.py):
  ```python
  # bypass cek authentication for development
  if http_userid == 'admin' and log.parent.level == logging.DEBUG:
      return user
  ```
- **Risk**: If `DEBUG` logging is enabled (common during staging or troubleshooting), any incoming RPC request with `HTTP_USERID: admin` skips HMAC signature verification entirely.
- **Action**: Remove the debug bypass or strictly gate behind an explicit mock testing fixture.

### 3. Overly Permissive Global CORS Headers
- **Issue**: In [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py), `add_cors_headers_response_callback` globally attaches:
  ```python
  'Access-Control-Allow-Origin': '*'
  'Access-Control-Allow-Methods': '*'
  'Access-Control-Allow-Headers': '*'
  ```
- **Risk**: Allows arbitrary external origins to make cross-origin requests to authenticated browser sessions.
- **Action**: Restrict CORS origins via configuration settings (`allowed_origin`).

### 4. Global CSRF Protection Disabled by Default
- **Issue**: In [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py), `config.set_default_csrf_options(require_csrf=False)` disables Pyramid's global CSRF protection across all views by default.
- **Action**: Enable CSRF globally by default and explicitly exempt only stateless API endpoints.

---

## 4. Code Quality, Modernization & Technical Debt

### 1. Python 3.12+ / 3.13 Compatibility Risks
- **`cgi.FieldStorage`**: Imported in [`opensipkd/base/views/base_views.py`](../opensipkd/base/views/base_views.py). The `cgi` module was deprecated in Python 3.11 and **completely removed in Python 3.13** (PEP 594).
- **`pkg_resources`**: Used in [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py) (`resource_filename`). This is deprecated; use standard library `importlib.resources`.

### 2. Monolithic Source Files
- [`opensipkd/base/views/base_views.py`](../opensipkd/base/views/base_views.py): 1,647 lines (62 KB)
- [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py): 893 lines (33 KB)
- [`opensipkd/base/views/user_login.py`](../opensipkd/base/views/user_login.py): 838 lines (33 KB)
- **Action**: Refactor into focused sub-modules (e.g. `crud.py`, `export.py`, `grid.py`).

### 3. Broad Exception Handling
- Bare `except:` blocks (e.g. Oracle client init in [`__init__.py`](../opensipkd/base/__init__.py)) suppress diagnostic errors during failed initialization.
- **Action**: Catch specific exceptions (`ImportError`, `oracledb.Error`) and log warnings.

---

## 5. Repository Hygiene & Packaging

- **Legacy Binaries & Backups**: The repository contains legacy backups in `bak/` containing executable binaries (`lpr.exe`), wheel files (`.whl`), and leftover build folders (`build/`, `tmp/`, `log_file/`, `2025/`).
- **Dependencies in `pyproject.toml`**: Dependencies are unpinned and include redundant packages like `"asyncio"` (standard library).

---

## 6. Actionable TODO List

### Priority: High (Security & Compatibility)
- [ ] **SEC-01**: Remove plaintext credentials from `development.ini` and implement environment variable loading (`os.environ` / `.env`).
- [ ] **SEC-02**: Remove the `http_userid == 'admin'` authentication bypass in [`opensipkd/base/tools/api.py`](../opensipkd/base/tools/api.py).
- [ ] **SEC-03**: Restrict CORS headers in [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py) using configured `allowed_origin` list.
- [ ] **SEC-04**: Review CSRF policy and enable CSRF tokens by default for non-API form submissions.
- [ ] **COMPAT-01**: Replace deprecated `cgi.FieldStorage` in [`base_views.py`](../opensipkd/base/views/base_views.py) with `multipart` or `webob` alternatives for Python 3.13 support.
- [ ] **COMPAT-02**: Replace `pkg_resources.resource_filename` with `importlib.resources` in [`opensipkd/base/__init__.py`](../opensipkd/base/__init__.py).

### Priority: Medium (Architecture & Quality)
- [ ] **CLEAN-01**: Remove `bak/`, `build/`, `tmp/`, `log_file/`, and binary files (`.whl`, `.exe`) from git tracking and update `.gitignore`.
- [ ] **CLEAN-02**: Clean up dependencies in [`pyproject.toml`](../pyproject.toml) (remove `"asyncio"`, pin sensible minimum versions for `pyramid`, `sqlalchemy`, `deform`).
- [ ] **TEST-01**: Migrate legacy tests from `bak/tests/` into an active `tests/` directory configured with `pytest` and `webtest`.
- [x] **CI-01**: Add CI/CD workflow (e.g. `.github/workflows/ci.yml` or GitLab CI) for automated syntax check, `pytest`, and `mypy`.

### Priority: Low (Refactoring & Maintenance)
- [ ] **REFACTOR-01**: Break down monolithic [`base_views.py`](../opensipkd/base/views/base_views.py) and [`__init__.py`](../opensipkd/base/__init__.py) into modular subcomponents.
- [ ] **REFACTOR-02**: Replace bare `except:` blocks with specific exception catching and informative logging.
