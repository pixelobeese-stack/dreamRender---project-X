#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np
import trimesh


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene")

    if isinstance(loaded, trimesh.Scene):
        mesh = loaded.dump(concatenate=True)
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    else:
        raise ValueError(f"Unsupported mesh type: {type(loaded)}")

    if mesh.is_empty or len(mesh.faces) == 0:
        raise ValueError("No mesh geometry found in input file.")

    return mesh


def normalize_mesh_to_grid(mesh: trimesh.Trimesh, grid_size: int, margin: float = 1.0) -> trimesh.Trimesh:
    mesh = mesh.copy()

    bounds = mesh.bounds
    center = (bounds[0] + bounds[1]) / 2.0
    extents = bounds[1] - bounds[0]
    max_extent = float(np.max(extents))

    if max_extent <= 0:
        raise ValueError("Input mesh has invalid bounds.")

    target_extent = max(float(grid_size - 1) - 2.0 * margin, 1.0)
    scale = target_extent / max_extent

    mesh.apply_translation(-center)
    mesh.apply_scale(scale)
    mesh.apply_translation(np.array([(grid_size - 1) / 2.0] * 3))

    return mesh


def voxelize(mesh: trimesh.Trimesh, grid_size: int, fill_volume: bool) -> np.ndarray:
    voxel_grid = mesh.voxelized(pitch=1.0)
    if fill_volume:
        voxel_grid = voxel_grid.fill()

    points = np.rint(voxel_grid.points).astype(int)
    points = np.clip(points, 0, grid_size - 1)

    if points.size == 0:
        return np.empty((0, 3), dtype=int)

    points = np.unique(points, axis=0)
    order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
    return points[order]


def build_output(points: np.ndarray, grid_size: int, color: str, output_format: str) -> dict:
    data = {
        "format": "dreamrender-voxels-v1",
        "gridSize": grid_size,
        "voxelCount": int(points.shape[0]),
    }

    if output_format in ("both", "dots"):
        data["dots"] = [
            {"x": int(p[0]), "y": int(p[1]), "z": int(p[2]), "color": color}
            for p in points
        ]

    if output_format in ("both", "map"):
        data["voxels"] = {f"{int(p[0])},{int(p[1])},{int(p[2])}": color for p in points}

    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert OBJ/GLTF/GLB files into 64x64x64 voxel JSON."
    )
    parser.add_argument("input", type=Path, help="Path to .obj, .gltf, or .glb file")
    parser.add_argument("output", type=Path, help="Output JSON file path")
    parser.add_argument("--grid-size", type=int, default=64, help="Target voxel grid size")
    parser.add_argument("--color", default="#8ecae6", help="Hex color to assign to every voxel")
    parser.add_argument(
        "--surface-only",
        action="store_true",
        help="Keep only surface voxels (default fills solid volume)",
    )
    parser.add_argument(
        "--format",
        choices=["both", "dots", "map"],
        default="both",
        help="Output only dot list, only key-map, or both",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.grid_size <= 0:
        raise ValueError("--grid-size must be a positive integer")

    suffix = args.input.suffix.lower()
    if suffix not in {".obj", ".gltf", ".glb"}:
        raise ValueError("Input file must be .obj, .gltf, or .glb")

    mesh = load_mesh(args.input)
    mesh = normalize_mesh_to_grid(mesh, grid_size=args.grid_size)
    points = voxelize(mesh, grid_size=args.grid_size, fill_volume=not args.surface_only)

    output_data = build_output(points, args.grid_size, args.color, args.format)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Wrote {output_data['voxelCount']} voxels to {args.output}")


if __name__ == "__main__":
    main()
