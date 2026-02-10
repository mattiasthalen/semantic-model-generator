# Phase 7: Fabric REST API Integration - Research

**Researched:** 2026-02-10
**Domain:** Microsoft Fabric REST APIs, semantic model deployment, long-running operations
**Confidence:** MEDIUM-HIGH

## Summary

Phase 7 integrates with Microsoft Fabric REST APIs to deploy semantic models programmatically. The core workflow involves: (1) resolving workspace and lakehouse/warehouse names to GUIDs via list APIs, (2) constructing Direct Lake URLs using GUID-based OneLake format, (3) base64-encoding TMDL files and packaging them into the Fabric API payload structure, (4) creating or updating semantic models via POST requests, and (5) polling long-running operations until completion.

The existing codebase already uses `azure-identity>=1.19` and `tenacity>=9.0` for authentication and retry logic, which are the standard tools for this domain. The project follows functional programming with frozen dataclasses, uses `mssql-python` for database connections, and Phase 5 already outputs TMDL as `dict[str, str]` (filename -> content) ready for base64 encoding.

**Primary recommendation:** Use `azure-identity.DefaultAzureCredential` for bearer token acquisition with scope `https://api.fabric.microsoft.com/.default`, standard `requests` library for HTTP calls, and implement LRO polling with exponential backoff using the existing `tenacity` dependency. Package TMDL as base64-encoded definition parts following the official Fabric API structure, and implement dev/prod naming aligned with Phase 6 patterns.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| azure-identity | >=1.19 | Azure authentication | Official Microsoft library, already in project dependencies, supports DefaultAzureCredential |
| requests | Latest | HTTP client for REST APIs | De facto standard for Python HTTP, simple bearer token auth, synchronous polling |
| tenacity | >=9.0 | Retry and backoff | Already in project dependencies, decorator-based, supports exponential backoff with jitter |
| base64 | stdlib | Base64 encoding | Python standard library, required for Fabric API payload encoding |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | JSON serialization | Building request payloads, parsing responses |
| datetime | stdlib | UTC timestamps | Dev mode naming with UTC timestamp suffix (aligned with Phase 6) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | httpx | httpx offers async support, but project is synchronous; requests is simpler |
| tenacity | backoff | backoff is lighter, but tenacity is already a dependency and more feature-complete |
| Manual retry | No retry | Unsafe for production; LRO polling requires robust retry with exponential backoff |

**Installation:**
```bash
# Already in pyproject.toml dependencies:
pip install azure-identity>=1.19 tenacity>=9.0
# Standard library (no install):
pip install requests  # Add to dependencies
```

## Architecture Patterns

### Recommended Module Structure
```
src/semantic_model_generator/
├── fabric/
│   ├── __init__.py
│   ├── auth.py           # Token acquisition using DefaultAzureCredential
│   ├── resolution.py     # Resolve workspace/lakehouse names to GUIDs
│   ├── packaging.py      # Base64 encode TMDL and build API payload
│   ├── deployment.py     # Create/update semantic model via REST API
│   └── polling.py        # LRO polling with exponential backoff
```

### Pattern 1: Authentication with DefaultAzureCredential
**What:** Use DefaultAzureCredential to acquire bearer tokens for Fabric REST API calls.
**When to use:** All Fabric API requests require authentication.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential
from azure.identity import DefaultAzureCredential

def get_fabric_token() -> str:
    """Acquire bearer token for Fabric REST API.

    Returns:
        Bearer token string (not including 'Bearer ' prefix)
    """
    credential = DefaultAzureCredential()
    # Fabric API scope must end with /.default
    token = credential.get_token("https://api.fabric.microsoft.com/.default")
    return token.token
```

### Pattern 2: Bearer Token Authorization Header
**What:** Include bearer token in Authorization header for all API requests.
**When to use:** Every request to api.fabric.microsoft.com.
**Example:**
```python
# Source: Multiple Python requests patterns
import requests

def call_fabric_api(endpoint: str, token: str, method: str = "GET", json_body: dict | None = None) -> requests.Response:
    """Make authenticated request to Fabric API.

    Args:
        endpoint: API endpoint path (e.g., "workspaces")
        token: Bearer token from get_fabric_token()
        method: HTTP method (GET, POST, PATCH)
        json_body: Optional JSON request body

    Returns:
        Response object
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://api.fabric.microsoft.com/v1/{endpoint}"

    if method == "GET":
        return requests.get(url, headers=headers)
    elif method == "POST":
        return requests.post(url, headers=headers, json=json_body)
    elif method == "PATCH":
        return requests.patch(url, headers=headers, json=json_body)
    else:
        raise ValueError(f"Unsupported method: {method}")
```

### Pattern 3: Workspace Name to GUID Resolution
**What:** List all workspaces and filter client-side by displayName to get workspace GUID.
**When to use:** User provides workspace name instead of GUID.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/list-workspaces
def resolve_workspace_id(workspace_name: str, token: str) -> str:
    """Resolve workspace name to GUID.

    Args:
        workspace_name: Workspace display name
        token: Bearer token

    Returns:
        Workspace GUID

    Raises:
        ValueError: If workspace not found or multiple matches
    """
    response = call_fabric_api("workspaces", token)
    response.raise_for_status()

    workspaces = response.json()["value"]
    matches = [ws for ws in workspaces if ws["displayName"] == workspace_name]

    if not matches:
        raise ValueError(f"Workspace '{workspace_name}' not found")
    if len(matches) > 1:
        raise ValueError(f"Multiple workspaces with name '{workspace_name}' found")

    return matches[0]["id"]
```

### Pattern 4: Lakehouse/Warehouse Name to GUID Resolution
**What:** List lakehouses or warehouses in workspace, filter by displayName to get item GUID.
**When to use:** User provides lakehouse/warehouse name instead of GUID.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/list-lakehouses
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/warehouse/items/list-warehouses
def resolve_lakehouse_id(workspace_id: str, lakehouse_name: str, token: str, item_type: str = "Lakehouse") -> str:
    """Resolve lakehouse or warehouse name to GUID.

    Args:
        workspace_id: Workspace GUID
        lakehouse_name: Lakehouse or warehouse display name
        token: Bearer token
        item_type: "Lakehouse" or "Warehouse"

    Returns:
        Lakehouse/warehouse GUID

    Raises:
        ValueError: If item not found or multiple matches
    """
    endpoint_map = {
        "Lakehouse": f"workspaces/{workspace_id}/lakehouses",
        "Warehouse": f"workspaces/{workspace_id}/warehouses"
    }
    endpoint = endpoint_map[item_type]

    response = call_fabric_api(endpoint, token)
    response.raise_for_status()

    items = response.json()["value"]
    matches = [item for item in items if item["displayName"] == lakehouse_name]

    if not matches:
        raise ValueError(f"{item_type} '{lakehouse_name}' not found in workspace")
    if len(matches) > 1:
        raise ValueError(f"Multiple {item_type}s with name '{lakehouse_name}' found")

    return matches[0]["id"]
```

### Pattern 5: Direct Lake URL Construction
**What:** Build GUID-based OneLake URL for Direct Lake connection.
**When to use:** After resolving workspace and lakehouse/warehouse GUIDs.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api
def build_direct_lake_url(workspace_id: str, lakehouse_id: str) -> str:
    """Construct GUID-based OneLake URL for Direct Lake.

    GUID-based URLs are stable across renames and don't require item type suffix.

    Args:
        workspace_id: Workspace GUID
        lakehouse_id: Lakehouse or warehouse GUID

    Returns:
        Direct Lake URL (e.g., https://onelake.dfs.fabric.microsoft.com/{workspaceGUID}/{itemGUID})

    Note:
        Phase 5 generates empty string for DirectLake expression URL.
        This function constructs the full URL for Phase 7 deployment.
    """
    return f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}"
```

### Pattern 6: TMDL Base64 Encoding and Packaging
**What:** Encode TMDL files to base64 and structure as Fabric API definition parts.
**When to use:** Before creating or updating semantic model via REST API.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition
import base64

def package_tmdl_for_fabric(tmdl_files: dict[str, str]) -> dict:
    """Package TMDL files as base64-encoded definition parts.

    Args:
        tmdl_files: Dict mapping relative paths to TMDL content (from Phase 5 generate_tmdl())

    Returns:
        Definition object with base64-encoded parts array

    Example input:
        {
            "definition/database.tmdl": "database\\n  compatibilityLevel: 1604\\n",
            "definition/model.tmdl": "model Model\\n  culture: en-US\\n",
            "definition.pbism": '{"version": "1.0"}',
            ".platform": '{"$schema": "..."}',
        }
    """
    parts = []
    for path, content in tmdl_files.items():
        # Encode string to bytes (UTF-8), then base64 encode
        content_bytes = content.encode('utf-8')
        payload_base64 = base64.b64encode(content_bytes).decode('ascii')

        parts.append({
            "path": path,
            "payload": payload_base64,
            "payloadType": "InlineBase64"
        })

    return {"parts": parts}
```

### Pattern 7: Create Semantic Model with LRO Handling
**What:** POST to create semantic model, handle 201 (immediate) or 202 (LRO) responses.
**When to use:** Deploying new semantic model to Fabric.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model
def create_semantic_model(
    workspace_id: str,
    display_name: str,
    definition: dict,
    token: str
) -> tuple[str, str | None]:
    """Create semantic model in Fabric workspace.

    Args:
        workspace_id: Workspace GUID
        display_name: Semantic model display name
        definition: Definition object from package_tmdl_for_fabric()
        token: Bearer token

    Returns:
        Tuple of (semantic_model_id, operation_id)
        - If 201: (semantic_model_id, None)
        - If 202: (None, operation_id) - poll operation, then get result

    Raises:
        requests.HTTPError: On API error
    """
    endpoint = f"workspaces/{workspace_id}/semanticModels"
    payload = {
        "displayName": display_name,
        "definition": definition
    }

    response = call_fabric_api(endpoint, token, method="POST", json_body=payload)
    response.raise_for_status()

    if response.status_code == 201:
        # Immediate completion
        result = response.json()
        return result["id"], None
    elif response.status_code == 202:
        # Long-running operation
        operation_id = response.headers.get("x-ms-operation-id")
        return None, operation_id
    else:
        raise ValueError(f"Unexpected status code: {response.status_code}")
```

### Pattern 8: Update Semantic Model Definition with LRO
**What:** POST to update existing semantic model definition, handle LRO.
**When to use:** Prod mode overwrite of existing semantic model.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/update-semantic-model-definition
def update_semantic_model_definition(
    workspace_id: str,
    semantic_model_id: str,
    definition: dict,
    token: str,
    update_metadata: bool = True
) -> str | None:
    """Update semantic model definition.

    Args:
        workspace_id: Workspace GUID
        semantic_model_id: Semantic model GUID
        definition: Definition object from package_tmdl_for_fabric()
        token: Bearer token
        update_metadata: If True, updates item metadata using .platform file

    Returns:
        Operation ID if 202 (LRO), None if 200 (immediate)
    """
    endpoint = f"workspaces/{workspace_id}/semanticModels/{semantic_model_id}/updateDefinition"
    if update_metadata:
        endpoint += "?updateMetadata=True"

    payload = {"definition": definition}

    response = call_fabric_api(endpoint, token, method="POST", json_body=payload)
    response.raise_for_status()

    if response.status_code == 200:
        return None
    elif response.status_code == 202:
        return response.headers.get("x-ms-operation-id")
    else:
        raise ValueError(f"Unexpected status code: {response.status_code}")
```

### Pattern 9: LRO Polling with Exponential Backoff
**What:** Poll operation status endpoint until completion, using Retry-After header and exponential backoff.
**When to use:** After receiving 202 response from create/update APIs.
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
import time

def is_operation_running(status: str | None) -> bool:
    """Check if operation is still running."""
    return status not in ("Succeeded", "Failed", None)

@retry(
    retry=retry_if_result(lambda result: result[0] == "Running"),
    stop=stop_after_attempt(60),  # Max 60 polls
    wait=wait_exponential(multiplier=1, min=2, max=30)
)
def poll_operation_status(operation_id: str, token: str) -> tuple[str, dict]:
    """Poll long-running operation until completion.

    Args:
        operation_id: Operation ID from x-ms-operation-id header
        token: Bearer token

    Returns:
        Tuple of (status, operation_data)
        - status: "Succeeded" or "Failed"
        - operation_data: Full operation response

    Raises:
        RuntimeError: If operation failed
    """
    endpoint = f"operations/{operation_id}"
    response = call_fabric_api(endpoint, token)
    response.raise_for_status()

    operation = response.json()
    status = operation["status"]

    # Honor Retry-After header if present
    retry_after = response.headers.get("Retry-After")
    if retry_after and status == "Running":
        time.sleep(int(retry_after))

    if status == "Failed":
        error = operation.get("error", {})
        raise RuntimeError(f"Operation failed: {error}")

    return status, operation

def get_operation_result(operation_id: str, token: str) -> dict:
    """Get result of completed operation.

    Args:
        operation_id: Operation ID
        token: Bearer token

    Returns:
        Result object (e.g., created semantic model)
    """
    endpoint = f"operations/{operation_id}/result"
    response = call_fabric_api(endpoint, token)
    response.raise_for_status()
    return response.json()
```

### Pattern 10: Dev Mode Naming with UTC Timestamp
**What:** Append UTC timestamp suffix to semantic model name in dev mode for safe iteration.
**When to use:** Dev mode deployment (aligned with Phase 6 folder naming).
**Example:**
```python
# Source: Phase 6 pattern (src/semantic_model_generator/output/writer.py)
from datetime import UTC, datetime

def get_deployment_name(model_name: str, dev_mode: bool = True, timestamp: str | None = None) -> str:
    """Get semantic model name with dev/prod mode support.

    Args:
        model_name: Base model name
        dev_mode: If True, appends timestamp suffix; if False, uses base name
        timestamp: Optional explicit timestamp in format "YYYYMMDDTHHMMSSz" (for testing)

    Returns:
        Deployment name

    Examples:
        >>> get_deployment_name("My Model", dev_mode=True, timestamp="20260210T120000Z")
        "My Model_20260210T120000Z"

        >>> get_deployment_name("My Model", dev_mode=False)
        "My Model"
    """
    if dev_mode:
        if timestamp is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return f"{model_name}_{timestamp}"

    return model_name
```

### Anti-Patterns to Avoid
- **Hardcoding workspace/lakehouse IDs:** Always support name-based resolution for usability
- **Ignoring LRO 202 responses:** Always implement polling; large models can take minutes
- **Manual retry without backoff:** Use tenacity with exponential backoff to avoid rate limits
- **Forgetting UTF-8 encoding:** Always `.encode('utf-8')` before base64 encoding strings
- **Interactive prompts in notebooks:** Use explicit parameters (e.g., `confirm_overwrite=True`) instead

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Azure authentication | Custom token cache, manual refresh | `DefaultAzureCredential` from azure-identity | Handles multiple credential sources, token caching, automatic refresh, works across environments |
| Exponential backoff | Sleep with manual doubling | `tenacity` with `wait_exponential` | Handles jitter, max delay, proper async sleep, already a dependency |
| LRO polling | While loop with sleep | `tenacity` retry decorators | Handles max attempts, exponential backoff, respects Retry-After header |
| Base64 encoding | Manual byte manipulation | `base64.b64encode()` from stdlib | Correct padding, RFC-compliant, handles edge cases |
| HTTP client with retries | Raw urllib with manual retry | `requests` + `tenacity` | Simple API, wide adoption, integrates cleanly with tenacity |

**Key insight:** Microsoft Fabric REST APIs follow Azure standards (bearer tokens, LRO patterns, error codes). Reusing Azure-standard libraries (azure-identity, requests, tenacity) minimizes custom code and follows ecosystem best practices.

## Common Pitfalls

### Pitfall 1: Not Handling Both Name and GUID Inputs
**What goes wrong:** Code only accepts GUIDs, forcing users to manually look up IDs in Fabric UI.
**Why it happens:** API requires GUIDs, so developers pass GUID requirement to users.
**How to avoid:**
- Accept `workspace_name_or_id: str` parameter
- Check if it's a valid GUID (UUID format)
- If not a GUID, resolve name to GUID via list API
- Same pattern for lakehouse/warehouse
**Warning signs:** Function signatures with only `workspace_id` parameters, documentation requiring users to "find workspace GUID in portal"

### Pitfall 2: Forgetting to Honor Retry-After Header
**What goes wrong:** Polling too aggressively triggers rate limits (429 errors), slowing down overall operation.
**Why it happens:** Exponential backoff implementation ignores Retry-After header from API.
**How to avoid:**
- Check for `Retry-After` header in LRO polling responses
- If present, sleep for specified seconds before next poll
- Combine with exponential backoff (use whichever is longer)
**Warning signs:** Frequent 429 errors during LRO polling, operations taking longer than expected

### Pitfall 3: Base64 Encoding Without UTF-8 Encoding First
**What goes wrong:** Non-ASCII characters in TMDL (e.g., table descriptions) cause encoding errors or garbled text.
**Why it happens:** `base64.b64encode()` requires bytes, but developers pass string directly or use wrong encoding.
**How to avoid:**
- Always: `content.encode('utf-8')` before `base64.b64encode()`
- Decode base64 result to ASCII string: `.decode('ascii')`
- Python 3 pattern: `base64.b64encode(content.encode('utf-8')).decode('ascii')`
**Warning signs:** UnicodeDecodeError, garbled characters in deployed models, errors with non-English table names

### Pitfall 4: Not Validating Operation Success Before Getting Result
**What goes wrong:** Calling `/result` endpoint before operation completes returns 404 or incomplete data.
**Why it happens:** Developer assumes 202 response means success, skips polling.
**How to avoid:**
- Always poll `/operations/{id}` until status is "Succeeded" or "Failed"
- Check status == "Succeeded" before calling `/operations/{id}/result`
- Handle "Failed" status by raising error with operation error details
**Warning signs:** Intermittent 404 errors, race conditions in deployment scripts

### Pitfall 5: Token Expiration During Long Operations
**What goes wrong:** LRO polling fails midway through with 401 Unauthorized.
**Why it happens:** Token acquired at start expires (typically 1 hour) during long-running deployment.
**How to avoid:**
- Refresh token before each API call, not just at start
- Or: Check token expiration, refresh if < 5 minutes remaining
- `DefaultAzureCredential.get_token()` handles caching and refresh automatically
**Warning signs:** 401 errors appearing after 30-60 minutes of polling

### Pitfall 6: Assuming Immediate Completion (201 Only)
**What goes wrong:** Code only handles 201 response, crashes on 202 (LRO).
**Why it happens:** Testing with small models returns 201, but production models trigger LRO.
**How to avoid:**
- Always handle both 201 (immediate) and 202 (LRO) responses
- Extract logic into separate functions: `handle_immediate_result()` and `handle_lro()`
- Test with large models to trigger LRO path
**Warning signs:** Works in dev, fails in prod; works with 1-table models, fails with 50-table models

### Pitfall 7: Dev Mode Creating Duplicate Models
**What goes wrong:** Multiple dev deployments with same timestamp overwrite each other.
**Why it happens:** Timestamp generated once at script start, multiple calls within same second.
**How to avoid:**
- Generate timestamp once per deployment, pass through call stack
- For testing: accept explicit `timestamp` parameter for reproducibility
- Align with Phase 6 pattern: `get_deployment_name()` accepts optional timestamp
**Warning signs:** Dev deployments randomly overwriting each other, test flakiness

### Pitfall 8: Missing Workspace/Lakehouse Permissions
**What goes wrong:** 401/403 errors despite valid token, or empty lists from list APIs.
**Why it happens:** Service principal or user lacks workspace contributor role or lakehouse read access.
**How to avoid:**
- Validate workspace exists AND user has contributor role before deployment
- Check list APIs return expected items before attempting create
- Provide clear error messages: "Workspace 'X' not found. Ensure you have contributor access."
**Warning signs:** Empty list responses, permission errors mid-deployment

## Code Examples

Verified patterns from official sources:

### Complete Deployment Flow (Dev Mode)
```python
# Source: Composite pattern from official Fabric API docs
from azure.identity import DefaultAzureCredential
import requests
import base64
from datetime import UTC, datetime

def deploy_semantic_model_dev(
    tmdl_files: dict[str, str],
    workspace_name: str,
    model_name: str
) -> str:
    """Deploy semantic model to Fabric in dev mode.

    Args:
        tmdl_files: TMDL files from Phase 5 generate_tmdl()
        workspace_name: Workspace display name
        model_name: Base model name

    Returns:
        Deployed semantic model ID
    """
    # Step 1: Get token
    credential = DefaultAzureCredential()
    token = credential.get_token("https://api.fabric.microsoft.com/.default").token

    # Step 2: Resolve workspace name to GUID
    workspace_id = resolve_workspace_id(workspace_name, token)

    # Step 3: Generate dev mode name with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    deployment_name = f"{model_name}_{timestamp}"

    # Step 4: Package TMDL as base64-encoded parts
    definition = package_tmdl_for_fabric(tmdl_files)

    # Step 5: Create semantic model
    semantic_model_id, operation_id = create_semantic_model(
        workspace_id, deployment_name, definition, token
    )

    # Step 6: Handle LRO if needed
    if operation_id:
        status, _ = poll_operation_status(operation_id, token)
        if status == "Succeeded":
            result = get_operation_result(operation_id, token)
            semantic_model_id = result["id"]

    return semantic_model_id
```

### Prod Mode with Overwrite Confirmation
```python
# Source: REQ-35 notebook-friendly confirmation pattern
def deploy_semantic_model_prod(
    tmdl_files: dict[str, str],
    workspace_name: str,
    model_name: str,
    confirm_overwrite: bool = False
) -> str:
    """Deploy semantic model to Fabric in prod mode.

    Args:
        tmdl_files: TMDL files from Phase 5
        workspace_name: Workspace display name
        model_name: Model name (no timestamp suffix)
        confirm_overwrite: REQUIRED explicit confirmation to overwrite existing model

    Returns:
        Deployed semantic model ID

    Raises:
        ValueError: If model exists and confirm_overwrite=False
    """
    # Get token and resolve workspace
    credential = DefaultAzureCredential()
    token = credential.get_token("https://api.fabric.microsoft.com/.default").token
    workspace_id = resolve_workspace_id(workspace_name, token)

    # Check if model already exists
    existing_id = find_semantic_model_by_name(workspace_id, model_name, token)

    if existing_id and not confirm_overwrite:
        raise ValueError(
            f"Semantic model '{model_name}' already exists in workspace '{workspace_name}'. "
            f"Pass confirm_overwrite=True to overwrite."
        )

    # Package TMDL
    definition = package_tmdl_for_fabric(tmdl_files)

    if existing_id:
        # Update existing model
        operation_id = update_semantic_model_definition(
            workspace_id, existing_id, definition, token
        )
        if operation_id:
            poll_operation_status(operation_id, token)
        return existing_id
    else:
        # Create new model
        semantic_model_id, operation_id = create_semantic_model(
            workspace_id, model_name, definition, token
        )
        if operation_id:
            status, _ = poll_operation_status(operation_id, token)
            if status == "Succeeded":
                result = get_operation_result(operation_id, token)
                semantic_model_id = result["id"]
        return semantic_model_id
```

### Resolving Direct Lake URL from Names
```python
# Source: REQ-16 name/GUID flexible resolution pattern
def resolve_direct_lake_url(
    workspace: str,
    lakehouse: str,
    token: str,
    item_type: str = "Lakehouse"
) -> str:
    """Resolve Direct Lake URL from workspace and lakehouse names or GUIDs.

    Args:
        workspace: Workspace name or GUID
        lakehouse: Lakehouse/warehouse name or GUID
        token: Bearer token
        item_type: "Lakehouse" or "Warehouse"

    Returns:
        GUID-based OneLake URL

    Example:
        >>> resolve_direct_lake_url("Analytics Workspace", "Sales Lakehouse", token)
        "https://onelake.dfs.fabric.microsoft.com/a1b2c3d4-.../x9y8z7w6-..."
    """
    # Resolve workspace (if name, get GUID)
    if is_guid(workspace):
        workspace_id = workspace
    else:
        workspace_id = resolve_workspace_id(workspace, token)

    # Resolve lakehouse (if name, get GUID)
    if is_guid(lakehouse):
        lakehouse_id = lakehouse
    else:
        lakehouse_id = resolve_lakehouse_id(workspace_id, lakehouse, token, item_type)

    # Build GUID-based URL
    return build_direct_lake_url(workspace_id, lakehouse_id)

def is_guid(value: str) -> bool:
    """Check if string is a valid GUID."""
    import re
    guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(guid_pattern, value.lower()))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PowerShell automation | Python SDK + REST API | 2024-2025 | Official Python support with mssql-python GA Jan 2026, Fabric REST APIs stable |
| XMLA endpoint for deployment | Fabric REST API with TMDL | 2024 | Native TMDL support, no XMLA complexity, better for Direct Lake models |
| Interactive token acquisition | DefaultAzureCredential | Ongoing | Supports service principals, managed identity, works in notebooks and CI/CD |
| Fixed retry delays | Exponential backoff with jitter | Industry standard | Reduces load during outages, avoids rate limits |
| TMSL format | TMDL format | 2023-2024 | Folder-based, modular, human-readable, better for version control |

**Deprecated/outdated:**
- **Power BI REST API for semantic models**: Fabric REST APIs supersede Power BI REST APIs for Fabric-hosted models
- **XMLA endpoint writes**: Still supported but Fabric REST API is preferred for Direct Lake models
- **Name-based OneLake URLs**: Still work but GUID-based URLs are more stable (immune to renames)

## Open Questions

1. **Connection Binding for Cross-Environment Deployment**
   - What we know: Fabric has a connection binding REST API (announced 2024-2025)
   - What's unclear: Does deployment automatically bind to target workspace's data sources, or do we need explicit connection binding API calls?
   - Recommendation: Start with basic deployment (Phase 7), validate connection behavior, add explicit binding in Phase 8 if needed (noted in roadmap)

2. **Rate Limiting Details**
   - What we know: API returns 429 with Retry-After header
   - What's unclear: Exact rate limits (requests per second/minute), per-user vs per-service-principal
   - Recommendation: Implement exponential backoff with tenacity, honor Retry-After, monitor for 429s in production

3. **Maximum Operation Duration**
   - What we know: Large models can take several minutes
   - What's unclear: Is there a maximum timeout (e.g., 30 minutes) after which LRO is cancelled?
   - Recommendation: Set reasonable max polling attempts (e.g., 60 attempts with exponential backoff = ~30min max), document observed timeouts during testing

4. **Model Size Limits**
   - What we know: Fabric supports large semantic models
   - What's unclear: Are there payload size limits for the definition parts array?
   - Recommendation: Test with large models (100+ tables) during Phase 7 implementation, document any observed limits

## Sources

### Primary (HIGH confidence)
- [Microsoft Fabric REST API - Create Semantic Model](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model) - Create endpoint, request/response structure, LRO handling
- [Microsoft Fabric REST API - Update Semantic Model Definition](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/update-semantic-model-definition) - Update endpoint, definition structure
- [Microsoft Fabric REST API - Long Running Operations](https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation) - LRO polling pattern, headers, status codes
- [Microsoft Fabric REST API - List Workspaces](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/list-workspaces) - Workspace resolution, response structure
- [Microsoft Fabric REST API - List Lakehouses](https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/list-lakehouses) - Lakehouse resolution, item structure
- [Microsoft Fabric REST API - List Warehouses](https://learn.microsoft.com/en-us/rest/api/fabric/warehouse/items/list-warehouses) - Warehouse resolution
- [Microsoft Fabric REST API - Scopes](https://learn.microsoft.com/en-us/rest/api/fabric/articles/scopes) - Authentication scopes for semantic models
- [Microsoft Fabric API Quickstart](https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/fabric-api-quickstart) - Token acquisition, authentication flow
- [OneLake URL Format](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api) - GUID-based vs name-based URLs
- [SemanticModel Definition - TMDL Format](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition) - TMDL parts structure, path conventions
- [Azure Identity - DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential) - Token acquisition, scope format

### Secondary (MEDIUM confidence)
- [Python base64 module documentation](https://docs.python.org/3/library/base64.html) - Base64 encoding best practices
- [Tenacity PyPI](https://pypi.org/project/backoff/) - Exponential backoff patterns for Python
- [Fabric API 101: Stitching Together Your First Call](https://www.advancinganalytics.co.uk/blog/fabric-rest-api-101-stitching-together-your-first-call) - Practical bearer token usage
- [Python Requests with Bearer Token Examples](https://apitest.newtum.com/examples/python-requests-with-bearer-token) - Authorization header patterns
- [Microsoft Fabric Resource Naming Framework](https://medium.com/@valentin.loghin/microsoft-fabric-best-practice-and-naming-convention-d0550d83c0a1) - Naming conventions for Fabric items

### Tertiary (LOW confidence - needs validation)
- [Microsoft Fabric community discussions on REST API errors](https://community.fabric.microsoft.com/) - Common error scenarios, workarounds
- [Fabric Deployment Pipelines](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/understand-the-deployment-process) - Environment naming considerations (but pipelines expect name parity, so timestamp suffix aligns with separate dev workspace pattern)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - azure-identity and tenacity already in dependencies, requests is industry standard, official Microsoft docs verify all patterns
- Architecture: MEDIUM-HIGH - Official API docs are comprehensive, but production edge cases (rate limits, large models, connection binding) need validation during implementation
- Pitfalls: MEDIUM - Based on official docs, common REST API patterns, and Phase 6 alignment, but some pitfalls are preventative (not observed in wild)
- Direct Lake URL resolution: HIGH - Official Microsoft docs clearly specify GUID-based format
- TMDL packaging: HIGH - Official API docs specify exact base64 and parts structure
- LRO polling: HIGH - Official docs provide complete pattern with examples
- Authentication: HIGH - Azure-identity is official library, scope format verified in docs
- Connection binding: LOW - Announced but not yet validated in practice (flagged as Phase 7/8 concern in roadmap)

**Research date:** 2026-02-10
**Valid until:** 2026-03-12 (30 days - Fabric REST APIs are stable, but features evolve monthly)
