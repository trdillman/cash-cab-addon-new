import bpy
import json
from collections import Counter
from pathlib import Path

scene_path = bpy.path.abspath('//extend_test.blend')
if Path(scene_path).exists():
    bpy.ops.wm.open_mainfile(filepath=scene_path)

summary = {}
scene = bpy.context.scene

# Helper to gather object names within a collection
def collection_objects(coll):
    if not coll:
        return []
    return sorted(obj.name for obj in coll.objects)

summary['scene'] = scene.name
summary['total_objects'] = len(bpy.data.objects)

# Collections of interest
for coll_name in (
    'ASSET_BUILDINGS',
    'ASSET_ROADS',
    'ASSET_WATER',
    'ASSET_ISLAND',
    '.other',
    'map_extend.osm',
    'way_profiles',
):
    coll = bpy.data.collections.get(coll_name)
    summary[f'collection_{coll_name}'] = {
        'exists': coll is not None,
        'object_count': len(coll.objects) if coll else 0,
        'children': sorted(child.name for child in coll.children) if coll else [],
        'objects': collection_objects(coll)[:10],
    }

# Key objects
for obj_name in ('BUILDINGS', 'ASSET_ROADS', 'ASSET_WATER', 'ASSET_ISLAND'):
    obj = bpy.data.objects.get(obj_name)
    entry = {
        'exists': obj is not None,
    }
    if obj and hasattr(obj.data, 'polygons'):
        entry['polygon_count'] = len(obj.data.polygons)
    summary[f'object_{obj_name}'] = entry

# Duplicate object names
counts = Counter(obj.name for obj in bpy.data.objects)
summary['duplicate_object_names'] = sorted(name for name, count in counts.items() if count > 1)

# BUILDINGS variants
summary['building_name_variants'] = sorted(name for name in counts if name.startswith('BUILDINGS'))

# Check map collection view layer exclusion
map_coll = bpy.data.collections.get('map_extend.osm')
layer_info = []
if map_coll:
    def walk(layer_coll):
        if layer_coll.collection == map_coll:
            layer_info.append({
                'view_layer': layer_coll.id_data.name,
                'exclude': layer_coll.exclude,
                'hide_viewport': layer_coll.hide_viewport,
            })
        for child in layer_coll.children:
            walk(child)
    for view_layer in bpy.context.scene.view_layers:
        walk(view_layer.layer_collection)
summary['map_extend_view_layers'] = layer_info

print(json.dumps(summary, indent=2))
