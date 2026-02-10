# Phase 6: Output Layer - Research

**Researched:** 2026-02-10
**Domain:** File system output management, watermark-based file protection, atomic file writing, cross-platform file handling
**Confidence:** HIGH

## Summary

Phase 6 implements the output layer that writes generated TMDL to disk with watermark-based protection for manually-maintained files. The research confirms that Python's standard library provides all necessary tools: pathlib for directory creation, os.replace for atomic file updates, and tempfile for safe temporary file handling. The watermark pattern is well-established in code generation tools, with Go standardizing on "Code generated ... DO NOT EDIT" and other ecosystems using similar conventions.

The implementation requires three main components: (1) watermark generation and detection using simple string containment checks, (2) atomic file writing using tempfile + os.replace to prevent corruption, and (3) result summarization to report what changed. Python's pathlib.Path.mkdir(parents=True, exist_ok=True) handles directory creation safely. For atomic writes, the pattern is: write to temporary file in same directory → os.replace() to atomically swap files → only committed writes survive.

The dev vs prod mode distinction is straightforward: dev mode appends UTC timestamp to folder name (ISO 8601 compact format), prod mode requires explicit overwrite flag. The watermark uses TMDL's triple-slash (///) comment syntax for .tmdl files and appropriate comment syntax for JSON files (dedicated "_comment" field). File encoding must be UTF-8 with explicit encoding parameter for cross-platform compatibility.

**Primary recommendation:** Use dataclass for WriteSummary return type, implement atomic writes with tempfile.NamedTemporaryFile(delete=False) + os.replace(), detect watermarks with simple "semantic-model-generator" substring check, use Path.mkdir(parents=True, exist_ok=True) for directories, and format UTC timestamps with datetime.utcnow().strftime("%Y%m%dT%H%M%SZ").

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Watermark design:**
- Multi-line header block at the top of every generated file
- Includes generator name, version, and UTC timestamp
- Uses TMDL triple-slash comment syntax (`///`) for .tmdl files
- Detection: file is considered auto-generated if it contains the string `semantic-model-generator` in a comment line
- Non-TMDL files (.pbism, .json, .platform): Claude's discretion on comment syntax appropriate for each format

**Overwrite behavior:**
- Files with watermark are overwritten on regeneration
- Files without watermark are skipped (preserved) and included in summary as "skipped (manually maintained)"
- Removing the watermark is the intentional signal to protect a file from regeneration
- Extra files on disk that are NOT in the generated output set are left untouched (not deleted)
- Writer returns a summary data structure listing: files written, files skipped (manually maintained), files unchanged
- Output directory is created automatically (mkdir -p) if it doesn't exist

**Dev vs prod mode:**
- Dev mode is the default when caller doesn't specify
- Dev mode appends ISO compact timestamp suffix: `ModelName_20260210T120000Z`
- Each dev run creates a new folder; no automatic cleanup of old dev folders
- Prod mode writes to the base model name folder
- Prod mode requires explicit `overwrite=True` flag when folder already exists; errors otherwise

**Folder structure:**
- Writer accepts any user-provided output path (no default lakehouse assumption)
- Folder name uses the exact model name as provided, preserving case and spaces
- Internal structure matches Fabric's TMDL spec: `definition/` subdirectory for .tmdl files, `.pbism` and `.platform` at root level
- Writer accepts the Phase 5 `dict[str, str]` output directly (filename-to-content mapping)

### Claude's Discretion

- Comment syntax for watermark in non-TMDL files (.json, .pbism, .platform)
- Exact header block formatting and line count
- Summary data structure design (dataclass, TypedDict, etc.)
- Error messages for prod mode overwrite rejection

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib (stdlib) | 3.11+ | Directory and file path handling | Modern Python path API, cross-platform, mkdir(parents=True, exist_ok=True) creates directories safely |
| datetime (stdlib) | 3.11+ | UTC timestamp generation for watermarks and dev mode | Built-in ISO 8601 formatting, utcnow() for consistent timestamps |
| tempfile (stdlib) | 3.11+ | Temporary file creation for atomic writes | NamedTemporaryFile with dir parameter ensures same filesystem for atomic rename |
| os (stdlib) | 3.11+ | Atomic file replacement with os.replace() | Cross-platform atomic rename, replaces destination atomically on Python 3.3+ |
| dataclasses (stdlib) | 3.11+ | WriteSummary result type | Type-safe return values, immutable with frozen=True, better than dict |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Phase 5 generate_all_tmdl() | - | TMDL content generation | Input to writer - dict[str, str] mapping file paths to content |
| hatch-vcs version | - | Generator version for watermark | Watermark includes version string for traceability |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| os.replace() | shutil.move() | shutil.move() lacks explicit atomicity guarantees; os.replace() is atomic and cross-platform |
| tempfile in same dir | tempfile in system temp | Cross-filesystem moves aren't atomic; same directory required for os.replace() atomicity |
| Dataclass | TypedDict | TypedDict is for dictionaries; dataclass provides attribute access, validation, and frozen immutability |
| Simple string check | Regex watermark detection | User explicitly requested simple string containment ("keep it predictable") |
| pathlib | os.path | os.path is string manipulation; pathlib is object-oriented, cleaner API |

**Installation:**
```bash
# No external dependencies needed - all stdlib
python --version  # Ensure >= 3.11
```

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── output/                  # NEW - Output layer module
│   ├── __init__.py
│   ├── writer.py           # Main write_tmdl_folder() function
│   └── watermark.py        # Watermark generation and detection
├── tmdl/                    # Existing from Phase 5
│   ├── generate.py         # generate_all_tmdl() produces dict[str, str]
│   └── metadata.py
└── utils/                   # Existing
    └── ...
```

### Pattern 1: Atomic File Writing with Temporary File
**What:** Write to temporary file in same directory, then atomically replace target with os.replace()
**When to use:** All file writes where corruption risk exists (system crash, disk full, etc.)
**Example:**
```python
# Source: https://alexwlchan.net/2019/atomic-cross-filesystem-moves-in-python/
# Source: https://docs.python.org/3/library/os.html#os.replace
import os
import tempfile
from pathlib import Path

def write_file_atomically(path: Path, content: str) -> None:
    """Write content to file atomically using temporary file."""
    # Create temp file in same directory for atomic rename
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )

    try:
        # Write to temp file
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Atomic replace
        os.replace(temp_path, path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise
```

### Pattern 2: Watermark Header Generation
**What:** Multi-line comment header at top of file with generator name, version, timestamp
**When to use:** Every generated file - enables detection for overwrite protection
**Example:**
```python
# Source: User decision from CONTEXT.md
# Source: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
from datetime import datetime, timezone

def generate_watermark_tmdl(version: str) -> str:
    """Generate watermark header for .tmdl files.

    Args:
        version: Generator version from hatch-vcs

    Returns:
        Multi-line triple-slash comment block
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return f"""/// Auto-generated by semantic-model-generator v{version}
/// Generated: {timestamp}
/// DO NOT EDIT - remove this header to protect from regeneration
"""

def generate_watermark_json(version: str) -> dict[str, str]:
    """Generate watermark metadata for JSON files.

    Args:
        version: Generator version from hatch-vcs

    Returns:
        Dict with _comment field for JSON inclusion
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "_comment": f"Auto-generated by semantic-model-generator v{version} at {timestamp}. DO NOT EDIT - remove this field to protect from regeneration."
    }
```

### Pattern 3: Watermark Detection
**What:** Simple string containment check for "semantic-model-generator" marker
**When to use:** Before writing each file - determines overwrite vs preserve
**Example:**
```python
# Source: User decision from CONTEXT.md (simple string containment, not regex)

def is_auto_generated(content: str) -> bool:
    """Check if file content contains auto-generation watermark.

    Args:
        content: File content as string

    Returns:
        True if watermark detected (safe to overwrite)
    """
    return "semantic-model-generator" in content
```

### Pattern 4: Directory Creation with Safe Defaults
**What:** Create nested directories with parents=True, exist_ok=True
**When to use:** Before writing files to ensure parent directories exist
**Example:**
```python
# Source: https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Create directory and all parent directories if needed.

    Args:
        path: Directory path to create
    """
    path.mkdir(parents=True, exist_ok=True)
```

### Pattern 5: WriteSummary Result Type
**What:** Frozen dataclass return type with categorized file lists
**When to use:** Return value from write_tmdl_folder() - clear summary of what changed
**Example:**
```python
# Source: User decision from CONTEXT.md (summary data structure)
# Source: https://docs.python.org/3/library/dataclasses.html
from dataclasses import dataclass

@dataclass(frozen=True)
class WriteSummary:
    """Summary of write_tmdl_folder() operation.

    Attributes:
        written: Files that were created or overwritten (had watermark)
        skipped: Files that were skipped (no watermark, manually maintained)
        unchanged: Files that were unchanged (content identical to existing)
        output_path: Final output folder path (includes timestamp for dev mode)
    """
    written: tuple[str, ...]
    skipped: tuple[str, ...]
    unchanged: tuple[str, ...]
    output_path: Path
```

### Pattern 6: Dev vs Prod Mode with Timestamp Suffix
**What:** Dev mode appends UTC timestamp to folder name for safe iteration
**When to use:** Default mode for development; prod mode requires explicit flag
**Example:**
```python
# Source: User decision from CONTEXT.md (ISO compact timestamp)
# Source: https://docs.python.org/3/library/datetime.html
from datetime import datetime, timezone
from pathlib import Path

def get_output_folder(
    base_path: Path,
    model_name: str,
    dev_mode: bool = True
) -> Path:
    """Determine output folder path based on mode.

    Args:
        base_path: User-specified output directory
        model_name: Model name (preserved exactly with case and spaces)
        dev_mode: If True, append timestamp; if False, use base name

    Returns:
        Full output folder path
    """
    if dev_mode:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        folder_name = f"{model_name}_{timestamp}"
    else:
        folder_name = model_name

    return base_path / folder_name
```

### Anti-Patterns to Avoid
- **Cross-filesystem temporary files:** tempfile must be in same directory as target for atomic rename
- **Regex watermark detection:** User requested simple string containment for predictability
- **Spaces in indentation:** TMDL requires tabs, but output layer writes content as-is from Phase 5
- **Implicit UTF-8 encoding:** Always specify encoding='utf-8' explicitly for cross-platform compatibility
- **Mutable return types:** WriteSummary should be frozen dataclass, not modifiable dict

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file writing | Manual temp file + rename logic | tempfile.mkstemp() + os.replace() | Edge cases: permissions, cleanup on error, same-filesystem requirement |
| Directory creation | Recursive mkdir with error handling | Path.mkdir(parents=True, exist_ok=True) | Built-in handles race conditions, missing parents, existing directories |
| UTC timestamp formatting | String concatenation or custom formatting | datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") | ISO 8601 compliance, timezone handling, zero-padding |
| File encoding detection | Charset detection libraries | Explicit encoding='utf-8' parameter | Output is always UTF-8, no detection needed |
| Watermark parsing | JSON parsing or YAML parsing for comments | Simple substring check: "semantic-model-generator" in content | User explicitly requested simple string containment |

**Key insight:** File I/O has many edge cases (permissions, disk space, crashes mid-write, filesystem differences). Standard library functions handle these correctly; custom implementations miss edge cases.

## Common Pitfalls

### Pitfall 1: Cross-Filesystem Temporary Files Breaking Atomicity
**What goes wrong:** Using system temp directory (/tmp) for temporary file, then os.replace() to different filesystem fails or becomes non-atomic copy operation
**Why it happens:** tempfile.NamedTemporaryFile() defaults to system temp directory, which may be different filesystem than target
**How to avoid:** Always pass dir=target.parent to tempfile functions to ensure same filesystem
**Warning signs:** os.replace() raising OSError with "Invalid cross-device link" or file corruption on crash

### Pitfall 2: Forgetting to Remove Temporary Files on Error
**What goes wrong:** Exception during write leaves .tmp files littering the output directory
**Why it happens:** No cleanup in exception handler, or NamedTemporaryFile(delete=True) tries to delete before os.replace()
**How to avoid:** Use try/except/finally with manual os.unlink(temp_path) in except block, or NamedTemporaryFile(delete=False) with explicit cleanup
**Warning signs:** .tmp files accumulating in output directory after errors

### Pitfall 3: Implicit File Encoding Breaking Cross-Platform Compatibility
**What goes wrong:** Files written on Linux (UTF-8 default) can't be read on Windows (CP1252 default) or vice versa
**Why it happens:** open() without encoding parameter uses platform default
**How to avoid:** Always specify encoding='utf-8' and newline='\n' explicitly
**Warning signs:** UnicodeDecodeError when reading files on different platform, or wrong characters displayed

### Pitfall 4: Overwriting Files Without Checking Watermark
**What goes wrong:** Manually-maintained files get overwritten, destroying user's work
**Why it happens:** Not reading existing file before writing, or watermark check logic error
**How to avoid:** Always read existing file (if exists), check watermark, add to skipped list if no watermark
**Warning signs:** User reports "my changes disappeared after regeneration"

### Pitfall 5: Not Handling Existing Directory in Prod Mode
**What goes wrong:** Prod mode silently overwrites existing model folder without confirmation
**Why it happens:** Not checking if folder exists before writing in prod mode
**How to avoid:** Check Path.exists() in prod mode, raise error if exists and overwrite=False
**Warning signs:** Accidental overwrites in production, no audit trail

### Pitfall 6: Modifying Phase 5 Output Dict
**What goes wrong:** Adding watermarks to dict[str, str] modifies the input dict (mutable)
**Why it happens:** dict is mutable, prepending watermark modifies the string in place
**How to avoid:** Phase 5 returns dict, Phase 6 prepends watermark during write (not before)
**Warning signs:** Unit tests fail when checking Phase 5 output after calling Phase 6

## Code Examples

Verified patterns from official sources:

### Safe Directory Creation
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

def create_tmdl_structure(base: Path) -> None:
    """Create TMDL folder structure."""
    # Root directory
    base.mkdir(parents=True, exist_ok=True)

    # Subdirectories
    (base / "definition").mkdir(exist_ok=True)
    (base / "definition" / "tables").mkdir(exist_ok=True)
```

### Atomic File Write
```python
# Source: https://docs.python.org/3/library/tempfile.html
# Source: https://zetcode.com/python/os-replace/
import os
import tempfile
from pathlib import Path

def write_file_safe(path: Path, content: str) -> None:
    """Write content to file atomically."""
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory
    fd, temp_path_str = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=False  # We'll open with encoding parameter
    )

    temp_path = Path(temp_path_str)

    try:
        # Write content with explicit encoding
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # Atomic replace (overwrites destination)
        os.replace(temp_path, path)

    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise
```

### Read Existing File with Watermark Check
```python
# Source: User decision from CONTEXT.md
from pathlib import Path

def should_overwrite(path: Path) -> bool:
    """Check if file should be overwritten based on watermark.

    Args:
        path: File path to check

    Returns:
        True if file doesn't exist or has watermark (safe to overwrite)
        False if file exists without watermark (manually maintained)
    """
    if not path.exists():
        return True

    try:
        content = path.read_text(encoding='utf-8')
        return "semantic-model-generator" in content
    except Exception:
        # If we can't read it, assume it's manually maintained
        return False
```

### ISO 8601 Compact Timestamp
```python
# Source: https://docs.python.org/3/library/datetime.html
from datetime import datetime, timezone

def get_timestamp_suffix() -> str:
    """Generate ISO 8601 compact UTC timestamp for dev mode.

    Returns:
        Timestamp string like "20260210T120000Z"
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
```

### JSON Watermark with Comment Field
```python
# Source: https://dev.to/keploy/comments-in-json-workarounds-risks-and-best-practices-46ed
import json

def add_watermark_to_json(data: dict, version: str) -> str:
    """Add watermark to JSON data as _comment field.

    Args:
        data: JSON-serializable dict
        version: Generator version

    Returns:
        JSON string with watermark comment field
    """
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    watermarked = {
        "_comment": f"Auto-generated by semantic-model-generator v{version} at {timestamp}. DO NOT EDIT - remove this field to protect from regeneration.",
        **data
    }

    return json.dumps(watermarked, indent=2, ensure_ascii=False)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| shutil.move() for atomic writes | os.replace() with tempfile | Python 3.3+ (2012) | Explicit atomicity guarantee, better error handling |
| os.path string manipulation | pathlib object-oriented API | Python 3.4+ (2014) | Cleaner code, cross-platform, chainable operations |
| Platform-default encoding | Explicit encoding='utf-8' | Python 3.0+ (2008) | Cross-platform compatibility, no encoding bugs |
| Manual temp file handling | tempfile.mkstemp() / NamedTemporaryFile | Python 2.3+ (2003) | Secure temp files, automatic cleanup |
| Git-based watermarks | Simple substring detection | N/A | User decision - prioritizes predictability over sophistication |

**Deprecated/outdated:**
- Using open() without explicit encoding parameter - causes cross-platform bugs (Windows CP1252 vs Linux UTF-8)
- Using os.rename() instead of os.replace() - rename() has platform-specific error behavior
- Creating directories with os.makedirs() instead of Path.mkdir() - path objects cleaner

## Open Questions

1. **Should we validate TMDL content before writing?**
   - What we know: Phase 5 already validates with validate_tmdl_indentation()
   - What's unclear: Should Phase 6 re-validate as defensive programming?
   - Recommendation: Trust Phase 5 validation, don't duplicate. Phase 6 writes content as-is.

2. **How should we handle disk full errors?**
   - What we know: tempfile + os.replace prevents corruption
   - What's unclear: Should we catch OSError and provide helpful message?
   - Recommendation: Let OSError propagate with standard error message. Caller handles retry logic.

3. **Should WriteSummary include file sizes or timestamps?**
   - What we know: User wants "obvious what changed" summary
   - What's unclear: Are file paths sufficient, or should we include metadata?
   - Recommendation: Start with just file paths. Add metadata if users request it.

## Sources

### Primary (HIGH confidence)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - Path.mkdir() with parents and exist_ok
- [Python os documentation](https://docs.python.org/3/library/os.html#os.replace) - os.replace() atomicity guarantees
- [Python tempfile documentation](https://docs.python.org/3/library/tempfile.html) - mkstemp() and NamedTemporaryFile
- [Python datetime documentation](https://docs.python.org/3/library/datetime.html) - UTC timestamps and ISO 8601 formatting
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) - frozen dataclass pattern
- [TMDL triple-slash comment syntax](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) - /// for descriptions/comments

### Secondary (MEDIUM confidence)
- [Atomic file writing pattern](https://alexwlchan.net/2019/atomic-cross-filesystem-moves-in-python/) - tempfile + os.replace() approach
- [os.replace vs shutil.move comparison](https://zetcode.com/python/os-replace/) - atomicity guarantees
- [JSON comments workaround](https://dev.to/keploy/comments-in-json-workarounds-risks-and-best-practices-46ed) - _comment field pattern
- [Go code generation standard](https://github.com/golang/go/issues/13560) - "Code generated ... DO NOT EDIT" pattern

### Tertiary (LOW confidence)
- File permission handling with umask - not critical for this phase, output uses default permissions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, well-documented, stable APIs since Python 3.3+
- Architecture patterns: HIGH - Verified with official docs, cross-referenced multiple sources
- Pitfalls: MEDIUM-HIGH - Based on common file I/O issues and stdlib documentation

**Research date:** 2026-02-10
**Valid until:** 60 days (stable stdlib APIs, unlikely to change)
