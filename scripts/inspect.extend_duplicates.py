import bpy
import collections
scene_path = bpy.path.abspath('//extend_test.blend')
bpy.ops.wm.open_mainfile(filepath=scene_path)
counts = collections.Counter(obj.name for obj in bpy.data.objects)
dups = [name for name, count in counts.items() if count > 1]
print('duplicate object names:', dups)
sys.exit(0)
