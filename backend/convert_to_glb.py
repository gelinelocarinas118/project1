
import bpy
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"C:\Users\family\Desktop\sides\project1\backend\storage\app\public\outputs\20250516_151048\texturedMesh.obj")
bpy.ops.export_scene.gltf(filepath=r"C:\Users\family\Desktop\sides\project1\backend\storage\app\public\outputs\20250516_151048\20250516_151048_model.glb", export_format='GLB')
