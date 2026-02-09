"""Placeholder test to verify pytest and package installation work."""

import semantic_model_generator


def test_package_importable() -> None:
    """Verify that the package can be imported and has a version attribute."""
    assert hasattr(semantic_model_generator, "__version__")
    assert isinstance(semantic_model_generator.__version__, str)
