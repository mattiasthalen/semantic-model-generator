---
status: resolved
trigger: "fabric-notebook-auth-failure"
created: 2026-02-10T00:00:00Z
updated: 2026-02-10T00:35:00Z
---

## Current Focus

hypothesis: CONFIRMED - Authentication code doesn't detect Fabric notebook environment and lacks notebookutils integration
test: Implement environment detection and token acquisition for both SQL and REST API
expecting: Detection via sys.modules check for notebookutils, fallback to DefaultAzureCredential when not in notebook
next_action: Implement fix in fabric/auth.py and schema/connection.py

## Symptoms

expected: When running in Fabric notebook, should detect environment and use notebookutils.credentials.getToken("https://api.fabric.microsoft.com") for authentication
actual: DefaultAzureCredential attempts all standard auth methods (EnvironmentCredential, ManagedIdentityCredential, SharedTokenCacheCredential, AzureCliCredential, etc.) and fails with "Could not login because the authentication failed"
errors: |
  DefaultAzureCredential failed to retrieve a token from the included credentials.
  Attempted credentials:
      EnvironmentCredential: EnvironmentCredential authentication unavailable. Environment variables are not fully configured.
      ManagedIdentityCredential: ManagedIdentityCredential authentication unavailable, no response from the IMDS endpoint.
      SharedTokenCacheCredential: SharedTokenCacheCredential authentication unavailable. No accounts were found in the cache.
      AzureCliCredential: Azure CLI not found on path
      AzurePowerShellCredential: PowerShell is not installed
      AzureDeveloperCliCredential: Azure Developer CLI could not be found.

  RuntimeError: [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Could not login because the authentication failed.

  PipelineError: [connection] Failed to connect to 5dscrplirguurh56sz3vy633zu-xu7vpyhuygjutl5dgidcbqlrca.datawarehouse.fabric.microsoft.com
reproduction: Run semantic_model_generator.generate_semantic_model() in a Fabric notebook with valid SQL endpoint and database configured
started: User attempting to use the library in Fabric notebook - appears to be missing Fabric-specific authentication logic
context: User notes that Fabric can be detected by checking for existence of notebookutils module, and token should be obtained via notebookutils.credentials.getToken("https://api.fabric.microsoft.com")

## Eliminated

## Evidence

- timestamp: 2026-02-10T00:05:00Z
  checked: src/semantic_model_generator/fabric/auth.py
  found: get_fabric_token() only uses DefaultAzureCredential without any Fabric notebook detection
  implication: No environment detection for Fabric notebooks, will fail in notebook context

- timestamp: 2026-02-10T00:06:00Z
  checked: src/semantic_model_generator/schema/connection.py
  found: create_fabric_connection() uses ActiveDirectoryDefault which internally uses DefaultAzureCredential
  implication: Database connections also affected - both REST API and SQL connections fail in notebooks

- timestamp: 2026-02-10T00:10:00Z
  checked: .references/Semantic Model Generator.ipynb
  found: Reference notebook uses notebookutils.credentials.getToken("https://database.windows.net") for SQL connections and notebookutils.credentials.getToken("https://api.fabric.microsoft.com") for REST API
  implication: Notebook environment requires notebookutils token acquisition, not DefaultAzureCredential

- timestamp: 2026-02-10T00:12:00Z
  checked: Reference notebook authentication pattern
  found: Uses struct.pack to create SQL_COPT_SS_ACCESS_TOKEN attribute (1256) with UTF-16-LE encoded token
  implication: SQL connection needs token passed via attrs_before parameter with special encoding

## Resolution

root_cause: |
  The authentication system only uses DefaultAzureCredential which doesn't work in Fabric notebooks.
  Fabric notebooks require using notebookutils.credentials.getToken() for authentication.

  Two locations affected:
  1. fabric/auth.py: get_fabric_token() for REST API calls
  2. schema/connection.py: create_fabric_connection() for SQL warehouse connections

  Both need environment detection (check if notebookutils in sys.modules) and use appropriate auth method.

fix: |
  Added environment detection and notebook-specific authentication:

  1. fabric/auth.py:
     - Added _is_fabric_notebook() to detect notebook environment via sys.modules check
     - Modified get_fabric_token() to use notebookutils.credentials.getToken("https://api.fabric.microsoft.com") in notebooks
     - Fallback to DefaultAzureCredential when not in notebook

  2. schema/connection.py:
     - Added _is_fabric_notebook() for environment detection
     - Modified create_fabric_connection() to use notebookutils token for SQL in notebooks
     - Token encoded as UTF-16-LE and passed via attrs_before with SQL_COPT_SS_ACCESS_TOKEN (1256)
     - Fallback to ActiveDirectoryDefault when not in notebook

  3. Test coverage:
     - tests/fabric/test_auth.py: Added tests for notebook and non-notebook authentication paths
     - tests/schema/test_connection.py: Added tests for notebook SQL authentication with token struct validation

verification: |
  ✓ All 402 tests pass including new notebook authentication tests
  ✓ fabric/auth.py correctly detects and uses notebookutils in notebook environment
  ✓ schema/connection.py correctly formats token with UTF-16-LE encoding and SQL_COPT_SS_ACCESS_TOKEN
  ✓ Both modules fallback to DefaultAzureCredential when not in notebook
  ✓ No regressions in existing functionality

files_changed:
  - src/semantic_model_generator/fabric/auth.py
  - src/semantic_model_generator/schema/connection.py
  - tests/fabric/test_auth.py
  - tests/schema/test_connection.py
