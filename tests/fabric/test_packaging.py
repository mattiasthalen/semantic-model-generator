"""Tests for Fabric TMDL packaging module."""

import base64

from semantic_model_generator.fabric.packaging import package_tmdl_for_fabric


def test_package_single_file() -> None:
    """Test package_tmdl_for_fabric with single TMDL file."""
    tmdl_files = {"model.tmdl": "table MyTable"}

    result = package_tmdl_for_fabric(tmdl_files)

    assert "parts" in result
    assert len(result["parts"]) == 1


def test_package_multiple_files() -> None:
    """Test package_tmdl_for_fabric with multiple TMDL files."""
    tmdl_files = {
        "model.tmdl": "table MyTable",
        "expressions.tmdl": "expression MyExpression",
        "relationships.tmdl": "relationship MyRelationship",
    }

    result = package_tmdl_for_fabric(tmdl_files)

    assert "parts" in result
    assert len(result["parts"]) == 3


def test_package_base64_encoding() -> None:
    """Test package_tmdl_for_fabric correctly base64 encodes content."""
    content = "table MyTable"
    tmdl_files = {"model.tmdl": content}

    result = package_tmdl_for_fabric(tmdl_files)

    # Decode the base64 payload and verify it matches original content
    payload = result["parts"][0]["payload"]
    decoded = base64.b64decode(payload).decode("utf-8")
    assert decoded == content


def test_package_utf8_encoding() -> None:
    """Test package_tmdl_for_fabric with non-ASCII UTF-8 content."""
    content = "table Müller Über"
    tmdl_files = {"model.tmdl": content}

    result = package_tmdl_for_fabric(tmdl_files)

    # Decode and verify UTF-8 characters preserved
    payload = result["parts"][0]["payload"]
    decoded = base64.b64decode(payload).decode("utf-8")
    assert decoded == content


def test_package_path_preserved() -> None:
    """Test package_tmdl_for_fabric preserves file paths."""
    tmdl_files = {
        "model.tmdl": "content1",
        "subfolder/expressions.tmdl": "content2",
    }

    result = package_tmdl_for_fabric(tmdl_files)

    paths = {part["path"] for part in result["parts"]}
    assert "model.tmdl" in paths
    assert "subfolder/expressions.tmdl" in paths


def test_package_payload_type() -> None:
    """Test package_tmdl_for_fabric sets payloadType to InlineBase64."""
    tmdl_files = {
        "model.tmdl": "content1",
        "expressions.tmdl": "content2",
    }

    result = package_tmdl_for_fabric(tmdl_files)

    for part in result["parts"]:
        assert part["payloadType"] == "InlineBase64"


def test_package_empty_dict() -> None:
    """Test package_tmdl_for_fabric with empty input."""
    tmdl_files: dict[str, str] = {}

    result = package_tmdl_for_fabric(tmdl_files)

    assert "parts" in result
    assert len(result["parts"]) == 0


def test_package_structure() -> None:
    """Test package_tmdl_for_fabric returns correct structure."""
    tmdl_files = {"model.tmdl": "content"}

    result = package_tmdl_for_fabric(tmdl_files)

    # Result must have "parts" key containing a list
    assert isinstance(result, dict)
    assert "parts" in result
    assert isinstance(result["parts"], list)

    # Each part must have path, payload, payloadType
    for part in result["parts"]:
        assert "path" in part
        assert "payload" in part
        assert "payloadType" in part
