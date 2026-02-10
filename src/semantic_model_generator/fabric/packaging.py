"""Fabric TMDL packaging module."""

import base64


def package_tmdl_for_fabric(tmdl_files: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    """Package TMDL files as base64-encoded definition parts for Fabric API.

    Args:
        tmdl_files: Dict mapping relative paths to TMDL content
                    (from generate_all_tmdl()).

    Returns:
        Definition object with "parts" key containing list of
        {path, payload, payloadType} dicts.
    """
    parts: list[dict[str, str]] = []
    for path, content in tmdl_files.items():
        payload_base64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        parts.append(
            {
                "path": path,
                "payload": payload_base64,
                "payloadType": "InlineBase64",
            }
        )
    return {"parts": parts}
