"""Assimp Export Python Package"""

from .assimp_export_core import AssimpExporter

__version__ = "0.1.3"
__all__ = ["AssimpExporter", "usdz_to_obj"]


def usdz_to_obj(input_path, output_path):
    """Convert USDZ file to OBJ file"""
    exporter = AssimpExporter()
    exporter.usdz_to_obj(input_path, output_path)
