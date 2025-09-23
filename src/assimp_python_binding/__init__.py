"""Assimp Export Python Package"""

from .assimp_export_core import AssimpExporter

__version__ = "1.0.0"
__all__ = ["AssimpExporter", "usdz_to_obj"]


def usdz_to_obj(usdz_path: str, obj_path: str) -> bool:
    """Convert USDZ to OBJ format

    Args:
        usdz_path: Path to input USDZ file
        obj_path: Path to output OBJ file

    Returns:
        True if conversion successful, False otherwise
    """
    exporter = AssimpExporter()
    success = exporter.usdz_to_obj(usdz_path, obj_path)
    if not success:
        error = exporter.get_last_error()
        raise RuntimeError(f"Conversion failed: {error}")
    return success
