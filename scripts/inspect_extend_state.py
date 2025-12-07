import bpy
scene_path = bpy.path.abspath('//extend_test.blend')
bpy.ops.wm.open_mainfile(filepath=scene_path)
scene = bpy.context.scene
bbox = scene.get('blosm_import_bbox')
tiles = scene.get('blosm_import_tiles')
print('bbox:', bbox)
print('tiles count:', len(tiles) if tiles else 0)
print('tiles:', tiles)
print('extend_history:', scene.get('blosm_extend_history'))
