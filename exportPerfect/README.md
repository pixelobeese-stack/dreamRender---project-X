# exportPerfect

Convert `.obj`, `.gltf`, or `.glb` files into voxel JSON that fits a `64x64x64` grid.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python convert_to_voxels.py ./model.obj ./model.voxels.json
```

Optional flags:

- `--grid-size 64` target grid size (default `64`)
- `--color "#8ecae6"` color assigned to voxels
- `--fill-volume` fill interior voxels (requires `scipy`)
- `--format both|dots|map` output format control

## Output JSON

- `dots`: list of `{ x, y, z, color }`
- `voxels`: map of `"x,y,z" -> "#hex"`

Use `voxels` directly to rebuild a `Map` in your app.
