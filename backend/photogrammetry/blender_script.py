import bpy
import sys
import json
import os
from mathutils import Vector

bpy.context.scene.render.engine = 'BLENDER_EEVEE'


def parse_args():
    """
    blender -b -P blender_script.py -- <input.obj> <output.glb> <measurements.json>
        [target_height_cm] [--monochrome R G B]
    """
    argv = sys.argv[sys.argv.index("--") + 1:]
    if len(argv) < 3:
        raise SystemExit(
            "Usage: blender -b -P blender_script.py -- "
            "<input.obj> <output.glb> <measurements.json> "
            "[target_height_cm] [--monochrome R G B]"
        )

    input_model, output_glb, meas_json = argv[:3]

    target_height_cm = None
    if len(argv) >= 4 and not argv[3].startswith("--"):
        target_height_cm = float(argv[3])
        offset = 4
    else:
        offset = 3

    mono_rgb = None
    if "--monochrome" in argv[offset:]:
        idx = argv.index("--monochrome")
        try:
            r, g, b = map(float, argv[idx + 1: idx + 4])
        except ValueError:
            raise SystemExit("--monochrome expects three float values R G B (0-1)")
        mono_rgb = (r, g, b)

    return input_model, output_glb, meas_json, target_height_cm, mono_rgb


def load_measurements(path, override_height):
    with open(path, "r") as f:
        data = json.load(f)
    if override_height is not None:
        data["height_cm"] = override_height
    for key in ("height_cm", "shoulder_cm"):
        if key not in data:
            raise KeyError(f'"{key}" missing from {path}')
    return float(data["height_cm"]), float(data["shoulder_cm"])


def import_mesh(path):
    if not path.lower().endswith('.obj'):
        raise ValueError("Only .obj files are supported")
    bpy.ops.import_scene.obj(filepath=path)
    return bpy.context.selected_objects[0]


def object_dimensions(obj):
    bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    min_z, max_z = min(v.z for v in bbox), max(v.z for v in bbox)
    min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
    return max_z - min_z, max_x - min_x


def make_monochrome_material(rgb):
    """Create/reuse a single-colour Principled BSDF material."""
    name = f"Monochrome_{'_'.join(f'{c:.2f}' for c in rgb)}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def main():
    inp, outp, meas_json, target_height_cli, mono_rgb = parse_args()

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    obj = import_mesh(inp)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    meas_height_cm, meas_shoulder_cm = load_measurements(meas_json, target_height_cli)

    model_height_m, model_shoulder_m = object_dimensions(obj)
    model_height_cm = model_height_m * 100
    model_shoulder_cm = model_shoulder_m * 100

    sf_height = meas_height_cm / model_height_cm
    sf_shoulder = meas_shoulder_cm / model_shoulder_cm
    uniform_sf = min(sf_height, sf_shoulder)

    obj.scale = [s * uniform_sf for s in obj.scale]
    bpy.ops.object.transform_apply(scale=True)

    if mono_rgb is not None:
        mat = make_monochrome_material(mono_rgb)
        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                ob.data.materials.clear()
                ob.data.materials.append(mat)
        print(f"[BLENDER] Applied monochrome RGB={mono_rgb}")

    bpy.ops.export_scene.gltf(filepath=outp, export_format='GLB')

    if not os.path.isfile(outp):
        raise FileNotFoundError(f"Expected GLB at {outp}, but file not found!")
    print(f"[BLENDER] Verified GLB exists: {outp}")


if __name__ == "__main__":
    main()
