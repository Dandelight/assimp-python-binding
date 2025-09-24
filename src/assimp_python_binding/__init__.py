from __future__ import annotations

import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from .assimp_export_core import AssimpExporter

__version__ = "0.1.3"
__all__ = ["AssimpExporter", "usdz_to_obj"]


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _find_texture_in_usdz(usdz_path: Path) -> Optional[str]:
    """
    在 usdz(zip) 包内寻找贴图路径。优先返回 '0/baked_mesh_tex0.png'，
    若不存在，回退为第一个 .png 文件。
    返回 zip 内相对路径（使用 '/' 分隔）。
    """
    preferred = "0/baked_mesh_tex0.png"
    with zipfile.ZipFile(usdz_path, "r") as zf:
        names = zf.namelist()
        if preferred in names:
            return preferred
        for name in names:
            low = name.lower()
            if low.endswith(".png") and not low.endswith("/"):
                return name.replace("\\", "/")
    return None


def _extract_file_from_usdz(usdz_path: Path, member: str, dst_path: Path) -> None:
    _ensure_parent_dir(dst_path)
    with zipfile.ZipFile(usdz_path, "r") as zf:
        with zf.open(member) as src, open(dst_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


def _scale_obj_vertices(obj_path: Path, scale: float) -> None:
    """
    仅缩放顶点坐标 v x y z，其余（vt/vn/f 等）不变。
    """
    if scale == 1.0:
        return
    out_lines = []
    for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            # v x y z [w]
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1]) * scale
                    y = float(parts[2]) * scale
                    z = float(parts[3]) * scale
                    if len(parts) == 5:
                        w = parts[4]
                        out_lines.append(f"v {x} {y} {z} {w}")
                    else:
                        out_lines.append(f"v {x} {y} {z}")
                    continue
                except ValueError:
                    # 非法数值，保持原样
                    pass
        out_lines.append(line)
    obj_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def _ensure_mtllib(obj_path: Path, mtl_filename: str) -> None:
    """
    确保 OBJ 中存在 mtllib 指向给定 mtl 文件名；
    若已有 mtllib 行，则不更改其文件名（避免不必要改动）。
    若不存在，则在文件开头插入一行。
    """
    lines = obj_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    has_mtllib = any(l.strip().startswith("mtllib ") for l in lines)
    if not has_mtllib:
        lines.insert(0, f"mtllib {mtl_filename}")
        obj_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _replace_mtl_texture_path(mtl_path: Path, new_rel_path: str) -> None:
    """
    仅替换 map_Kd 的路径为 new_rel_path，其余内容保持不变。
    如存在多条 map_Kd，全部替换；若不存在则不添加。
    """
    pattern = re.compile(r"^(map_Kd\s+)(.+)$", re.IGNORECASE)
    out = []
    for line in mtl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pattern.match(line.strip())
        if m:
            prefix = m.group(1)
            out.append(f"{prefix}{new_rel_path}")
        else:
            out.append(line)
    mtl_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def usdz_to_obj(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    scale: float = 1.0,
    texture_rel: str = "0/baked_mesh_tex0.png",
) -> bool:
    """
    将 USDZ 导出为 OBJ，并在不改变其他 MTL 内容的前提下，仅替换贴图路径。
    额外提供 scale 参数控制 OBJ 顶点坐标缩放倍率（默认 1.0；例如 300 表示放大 300 倍）。

    处理流程：
    1) 使用 AssimpExporter 导出临时 OBJ（和可能的 MTL）。
    2) 缩放 OBJ 顶点坐标（v 行）。
    3) 确保 OBJ 引用了 MTL（mtllib），不强制改名。
    4) 从 USDZ 中提取纹理到临时目录的 texture_rel 路径。
    5) 仅替换 MTL 中 map_Kd 的路径为 texture_rel。
    6) 将处理后的 OBJ 复制到 output_path；另外打包一个 ZIP（obj、mtl、纹理）以便分发。

    返回 True/False 表示成功与否。
    """
    in_path = Path(input_path)
    out_obj = Path(output_path)
    _ensure_parent_dir(out_obj)

    with tempfile.TemporaryDirectory(prefix="usdz2obj_") as tmpdir:
        tmpdir = Path(tmpdir)
        name = out_obj.stem
        tmp_obj = tmpdir / f"{name}.obj"
        tmp_mtl = (
            tmpdir / f"{name}.mtl"
        )  # 常见导出器默认使用同名；若实际另有名字会在下文探测
        tmp_tex = tmpdir / texture_rel

        exporter = AssimpExporter(enable_logging=True)
        ok = exporter.usdz_to_obj(str(in_path), str(tmp_obj))
        if not ok or not tmp_obj.exists():
            err = ""
            try:
                err = exporter.get_last_error()
            except Exception:
                pass
            print(f"[usdz_to_obj] Assimp export failed. Error: {err}")
            return False

        # 寻找实际生成的 mtl 文件名（同目录下 *.mtl，优先同名）
        mtl_files = list(tmpdir.glob("*.mtl"))
        if (tmp_mtl.exists()) or mtl_files:
            # 选择实际存在的 mtl
            if not tmp_mtl.exists():
                # 若同名不存在，选第一个导出的 mtl
                tmp_mtl = mtl_files[0]
        else:
            # 未生成 mtl 则创建一个空壳（仅为挂载纹理路径）
            tmp_mtl.write_text("# auto-generated mtl\n", encoding="utf-8")

        # 1) 缩放 OBJ 顶点
        _scale_obj_vertices(tmp_obj, float(scale))

        # 2) 确保 OBJ 引用 MTL
        _ensure_mtllib(tmp_obj, tmp_mtl.name)

        # 3) 从 USDZ 提取纹理并写到指定相对路径
        tex_in_zip = _find_texture_in_usdz(in_path)
        if tex_in_zip is None:
            print(
                "[usdz_to_obj] Warning: no PNG texture found in USDZ; proceeding without texture."
            )
        else:
            _extract_file_from_usdz(in_path, tex_in_zip, tmp_tex)

        # 4) 仅替换 MTL 中的贴图路径
        _replace_mtl_texture_path(tmp_mtl, texture_rel)

        # 5) 生成 ZIP 包（包含 OBJ、MTL、纹理）
        out_zip = out_obj.with_suffix(".zip")
        _ensure_parent_dir(out_zip)
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(tmp_obj, arcname=tmp_obj.name)
            zf.write(tmp_mtl, arcname=tmp_mtl.name)
            if tmp_tex.exists():
                zf.write(tmp_tex, arcname=texture_rel)

        print(f"[usdz_to_obj] Done. OBJ: {out_obj}, ZIP: {out_zip}, scale={scale}")
        return True
