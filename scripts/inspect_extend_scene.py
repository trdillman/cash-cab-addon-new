import bpy
import sys
scene_path = bpy.path.abspath('//extend_test.blend')
if bpy.data.filepath != scene_path:
    bpy.ops.wm.open_mainfile(filepath=scene_path)
print('scene:', bpy.context.scene.name)
print('objects:', len(bpy.data.objects))
city_ext = bpy.data.collections.get('CITY_EXTENSIONS')
print('CITY_EXTENSIONS children:', [coll.name for coll in city_ext.children]) if city_ext else print('no city ext')
map_cols = [coll for coll in bpy.data.collections if coll.name.lower().startswith('map_')]
print('map collections (total):', len(map_cols))
for coll in map_cols:
    parents = [parent.name for parent in getattr(coll, 'users_collection', []) or [] if parent.name.startswith('Scene') or parent.name == '.other']
    print(f"  {coll.name} parents: {', '.join(parents) if parents else 'none'}")
other = bpy.data.collections.get('.other')
print('other collection children:', [child.name for child in other.children] if other else [])
print('buildings obj count:', len([obj for obj in bpy.data.objects if 'building' in obj.name.lower()]))
sys.exit(0)
