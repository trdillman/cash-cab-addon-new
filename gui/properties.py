"""
BLOSM Route Import - GUI Properties
Minimal property definitions for route import functionality only.
"""

import bpy

from ..asset_manager import AssetType

ASSET_TYPE_ITEMS = [
    (
        asset_type.value,
        asset_type.name.replace('_', ' ').title(),
        f"Save as {asset_type.name.replace('_', ' ').title()}"
    )
    for asset_type in AssetType
]

# Simplified - no 3D realistic mode in minimal version
_has3dRealistic = False


def _gather_selected_objects(context):
    if context is None:
        return []
    selected = list(getattr(context, "selected_objects", []) or [])
    active = getattr(context, "active_object", None)
    if active and active not in selected:
        selected.insert(0, active)
    return selected


def _asset_new_datablock_items(self, context):
    items = []
    type_value = getattr(self, "asset_new_type", AssetType.CAR.value)
    try:
        asset_type = AssetType(type_value)
    except ValueError:
        asset_type = AssetType.CAR

    seen = set()
    objects = _gather_selected_objects(context)

    object_types = {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}

    if asset_type in object_types:
        for obj in objects:
            if obj and obj.name not in seen:
                seen.add(obj.name)
                items.append((obj.name, obj.name, obj.type))
    elif asset_type == AssetType.MATERIAL:
        for obj in objects:
            for material in getattr(getattr(obj, 'data', None), 'materials', []) or []:
                if material and material.name not in seen:
                    seen.add(material.name)
                    items.append((material.name, material.name, "Material"))
        for material in bpy.data.materials:
            if material and material.name not in seen:
                seen.add(material.name)
                items.append((material.name, material.name, "Material"))
    elif asset_type == AssetType.NODE_GROUP:
        for obj in objects:
            for modifier in getattr(obj, 'modifiers', []) or []:
                if getattr(modifier, 'type', None) == 'NODES' and getattr(modifier, 'node_group', None):
                    name = modifier.node_group.name
                    if name not in seen:
                        seen.add(name)
                        items.append((name, name, "Geometry Nodes modifier"))
        for node_group in bpy.data.node_groups:
            if node_group and node_group.name not in seen:
                seen.add(node_group.name)
                items.append((node_group.name, node_group.name, node_group.type))
    elif asset_type == AssetType.WORLD:
        world = getattr(getattr(context, 'scene', None), 'world', None)
        if world:
            items.append((world.name, world.name, "Scene World"))
            seen.add(world.name)
        for world in bpy.data.worlds:
            if world and world.name not in seen:
                seen.add(world.name)
                items.append((world.name, world.name, "World"))
    elif asset_type == AssetType.COLLECTION:
        for obj in objects:
            for coll in getattr(obj, 'users_collection', []) or []:
                if coll and coll.name not in seen:
                    seen.add(coll.name)
                    items.append((coll.name, coll.name, "Collection"))
        for coll in bpy.data.collections:
            if coll and coll.name not in seen:
                seen.add(coll.name)
                items.append((coll.name, coll.name, "Collection"))

    if not items:
        return [("__NONE__", "<No match>", "No matching datablock found for the current selection")]
    return items


def _update_asset_new_type(self, context):
    items = _asset_new_datablock_items(self, context)
    if items:
        self.asset_new_datablock_storage = items[0][0]
        try:
            setattr(self, 'asset_new_datablock', 0)
        except Exception:
            pass
    else:
        self.asset_new_datablock_storage = "__NONE__"


def _asset_new_datablock_get(self):
    items = _asset_new_datablock_items(self, bpy.context)
    identifiers = [identifier for identifier, _, _ in items]
    stored = getattr(self, 'asset_new_datablock_storage', "__NONE__")
    if not identifiers:
        return 0
    if stored not in identifiers:
        return 0
    return identifiers.index(stored)


def _asset_new_datablock_set(self, value):
    try:
        index = int(value)
    except (TypeError, ValueError):
        return
    items = _asset_new_datablock_items(self, bpy.context)
    identifiers = [identifier for identifier, _, _ in items]
    if 0 <= index < len(identifiers):
        self.asset_new_datablock_storage = identifiers[index]


def getDataTypes(self, context):
    """Return available data types for import"""
    return [
        ("osm", "OpenStreetMap", "OpenStreetMap"),
        ("terrain", "terrain", "Terrain"),
    ]


class BlosmRouteWaypoint(bpy.types.PropertyGroup):
    """Single waypoint/stop address for route"""

    address: bpy.props.StringProperty(
        name="Waypoint Address",
        description="Intermediate stop address between start and end",
        default=""
    )


class BlosmDefaultLevelsEntry(bpy.types.PropertyGroup):
    """Entry for default building levels with weight"""

    levels: bpy.props.IntProperty(
        name="Levels",
        description="Default number of levels",
        default=5,
        min=1,
    )

    weight: bpy.props.IntProperty(
        name="Weight",
        description="Relative weight for random selection",
        default=100,
        min=1,
    )


class BlosmProperties(bpy.types.PropertyGroup):
    """Main property group for BLOSM route import addon"""

    # OSM Import settings
    dataType: bpy.props.EnumProperty(
        name="Data",
        items=getDataTypes,
        description="Data type for import",
        default=0,
    )

    mode: bpy.props.EnumProperty(
        name="Mode: 3D or 2D",
        items=(("3Dsimple", "3D", "3D"), ("2D", "2D", "2D")),
        description="Import data in 3D or 2D mode",
        default="3Dsimple",
    )

    osmSource: bpy.props.EnumProperty(
        name="Import OpenStreetMap from",
        items=(
            ("server", "server", "remote server"),
            ("file", "file", "file on the local disk"),
        ),
        description="From where to import OpenStreetMap data: remote server or a file on the local disk",
        default="server",
    )

    osmFilepath: bpy.props.StringProperty(
        name="OpenStreetMap file",
        subtype='FILE_PATH',
        description="Path to an OpenStreetMap file for import",
    )

    # Coordinate bounds
    minLat: bpy.props.FloatProperty(
        name="min lat",
        description="Minimum latitude of the imported extent",
        precision=4,
        min=-89.0,
        max=89.0,
        default=51.33,
    )

    maxLat: bpy.props.FloatProperty(
        name="max lat",
        description="Maximum latitude of the imported extent",
        precision=4,
        min=-89.0,
        max=89.0,
        default=51.33721,
    )

    minLon: bpy.props.FloatProperty(
        name="min lon",
        description="Minimum longitude of the imported extent",
        precision=4,
        min=-180.0,
        max=180.0,
        default=12.36902,
    )

    maxLon: bpy.props.FloatProperty(
        name="max lon",
        description="Maximum longitude of the imported extent",
        precision=4,
        min=-180.0,
        max=180.0,
        default=12.37983,
    )

    coordinatesAsFilter: bpy.props.BoolProperty(
        name="Use coordinates as filter",
        description="Use coordinates as a filter for the import from the file",
        default=False,
    )

    # Layer import toggles
    buildings: bpy.props.BoolProperty(
        name="Import buildings",
        description="Import building outlines",
        default=True,
    )

    water: bpy.props.BoolProperty(
        name="Import water",
        description="Import water objects (rivers and lakes)",
        default=True,
    )

    forests: bpy.props.BoolProperty(
        name="Import forests",
        description="Import forests and woods",
        default=True,
    )

    vegetation: bpy.props.BoolProperty(
        name="Import other vegetation",
        description="Import other vegetation (grass, meadow, scrub)",
        default=True,
    )

    highways: bpy.props.BoolProperty(
        name="Import roads and paths",
        description="Import roads and paths",
        default=True,
    )

    railways: bpy.props.BoolProperty(
        name="Import railways",
        description="Import railways",
        default=False,
    )

    # General settings
    terrainObject: bpy.props.StringProperty(
        name="Terrain",
        description="Blender object for the terrain",
    )

    singleObject: bpy.props.BoolProperty(
        name="Import as a single object",
        description="Import OSM objects as a single Blender mesh objects instead of separate ones",
        default=True,
    )

    relativeToInitialImport: bpy.props.BoolProperty(
        name="Relative to initial import",
        description="Import relative to the initial import if it is available",
        default=True,
    )

    setupScript: bpy.props.StringProperty(
        name="Setup script",
        subtype='FILE_PATH',
        description="Path to a setup script. Leave blank for default.",
    )

    loadMissingMembers: bpy.props.BoolProperty(
        name="Load missing members of relations",
        description=(
            "Relation members aren't contained in the OSM file if they are located outside of the OSM file extent. "
            "Enable this option to load the missing members of the relations either from a local file (if available) "
            "or from the server."
        ),
        default=True,
    )

    # Route address inputs
    route_start_address: bpy.props.StringProperty(
        name="Start Address",
        description="Starting address for route geocoding",
        default="1 Dundas St. E, Toronto",
    )

    route_end_address: bpy.props.StringProperty(
        name="End Address",
        description="Ending address for route geocoding",
        default="500 Yonge St, Toronto",
    )

    # Route geocoded coordinates (stored by geocoding service)
    route_start_address_lat: bpy.props.FloatProperty(
        name="Start Latitude",
        description="Latitude of start address (auto-populated)",
        default=0.0,
    )

    route_start_address_lon: bpy.props.FloatProperty(
        name="Start Longitude",
        description="Longitude of start address (auto-populated)",
        default=0.0,
    )

    route_end_address_lat: bpy.props.FloatProperty(
        name="End Latitude",
        description="Latitude of end address (auto-populated)",
        default=0.0,
    )

    route_end_address_lon: bpy.props.FloatProperty(
        name="End Longitude",
        description="Longitude of end address (auto-populated)",
        default=0.0,
    )

    # Route waypoints collection
    route_waypoints: bpy.props.CollectionProperty(
        type=BlosmRouteWaypoint,
        name="Route Waypoints",
        description="Intermediate stops between start and end",
    )

    route_padding_m: bpy.props.FloatProperty(
        name="Padding (m)",
        description="Padding in meters to expand the route bounding box",
        min=0.0,
        default=100.0,
    )

    # Route import toggles
    route_import_roads: bpy.props.BoolProperty(
        name="Import roads",
        description="Import OpenStreetMap roads for the route area",
        default=True,
    )

    route_import_buildings: bpy.props.BoolProperty(
        name="Import buildings",
        description="Import OpenStreetMap buildings for the route area",
        default=True,
    )

    route_enable_routecam: bpy.props.BoolProperty(
        name="Enable RouteCam Camera",
        description="Automatically create a cinematic RouteCam camera for the imported route",
        default=False,
    )

    route_extend_m: bpy.props.FloatProperty(
        name="Extend by (m)",
        description="Extend the imported city in all directions by this many meters",
        default=200.0,
        min=0.0,
        soft_max=5000.0,
    )

    route_import_water: bpy.props.BoolProperty(
        name="Import water",
        description="Import OpenStreetMap water features for the route area",
        default=True,
    )

    routecam_batch_v2_count: bpy.props.IntProperty(
        name="V2 Cameras",
        description="Number of random V2 (Robust Director) cameras to generate",
        default=2,
        min=0,
        max=10
    )

    routecam_batch_viz_count: bpy.props.IntProperty(
        name="Viz Cameras",
        description="Number of random Viz (Keyframe Viz) cameras to generate",
        default=2,
        min=0,
        max=10
    )

    route_create_preview_animation: bpy.props.BoolProperty(
        name="Create Animated Route & Assets",
        description="Generate a 250 frame animated preview along the imported route",
        default=True,
    )

    route_import_separate_tiles: bpy.props.BoolProperty(
        name="Import separate tiles",
        description="Import Overpass tiles separately for better alignment",
        default=False,
    )

    # UI toggles
    ui_show_animation: bpy.props.BoolProperty(
        name="Show Animation Controls",
        description="Toggle visibility of animation control section in the CashCab panel",
        default=False,
    )

    asset_apply_to_selection: bpy.props.BoolProperty(
        name="Apply to active selection",
        description="When enabled, assign appended materials/node groups to the active object",
        default=False,
    )

    # Fallback building heights (used by route buildings)
    levelHeight: bpy.props.FloatProperty(
        name="Level height",
        description=(
            "Average height of a level in meters to use for OSM tags building:levels and building:min_level"
        ),
        default=5.0,
    )

    defaultLevels: bpy.props.CollectionProperty(type=BlosmDefaultLevelsEntry)

    defaultLevelsIndex: bpy.props.IntProperty(
        subtype='UNSIGNED',
        default=0,
        description="Index of the active entry for the default number of levels",
    )

    asset_new_id: bpy.props.StringProperty(
        name="Asset ID",
        description="Unique identifier for a new asset entry",
        default="",
    )

    asset_new_name: bpy.props.StringProperty(
        name="Display Name",
        description="Human readable name for the asset",
        default="",
    )

    asset_new_type: bpy.props.EnumProperty(
        name="Asset Type",
        items=ASSET_TYPE_ITEMS,
        update=_update_asset_new_type,
        default=AssetType.CAR.value,
    )

    asset_new_datablock_storage: bpy.props.StringProperty(
        default="__NONE__",
        options={'SKIP_SAVE'},
    )

    asset_new_datablock: bpy.props.EnumProperty(
        name="Source",
        items=_asset_new_datablock_items,
        description="Which datablock from the current blend to capture",
        get=_asset_new_datablock_get,
        set=_asset_new_datablock_set,
    )

    asset_new_blend_path: bpy.props.StringProperty(
        name="Blend File",
        subtype='FILE_PATH',
        description="Blend file that stores the asset",
        default="",
    )

    asset_new_collection: bpy.props.StringProperty(
        name="Collection",
        description="Optional collection to link appended objects into",
        default="",
    )

    asset_active_id: bpy.props.StringProperty(
        name="Active Asset",
        description="ID of the asset currently selected for editing",
        default="",
    )

    asset_edit_name: bpy.props.StringProperty(
        name="Name",
        description="Display name for the selected asset",
        default="",
    )

    asset_edit_description: bpy.props.StringProperty(
        name="Description",
        description="Optional description for the asset",
        default="",
    )

    asset_edit_blend_path: bpy.props.StringProperty(
        name="Blend File",
        subtype='FILE_PATH',
        description="Blend file that stores the asset",
        default="",
    )

    asset_edit_datablock: bpy.props.StringProperty(
        name="Datablock",
        description="Datablock name to append or link",
        default="",
    )

    asset_edit_collection: bpy.props.StringProperty(
        name="Collection",
        description="Collection to link appended objects into",
        default="",
    )

    asset_edit_tags: bpy.props.StringProperty(
        name="Tags",
        description="Comma-separated tags for filtering and roles",
        default="",
    )

    asset_edit_location: bpy.props.FloatVectorProperty(
        name="Location",
        description="Default location applied on append",
        default=(0.0, 0.0, 0.0),
    )

    asset_edit_rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        description="Default Euler rotation applied on append",
        default=(0.0, 0.0, 0.0),
    )

    asset_edit_scale: bpy.props.FloatVectorProperty(
        name="Scale",
        description="Default scale applied on append",
        default=(1.0, 1.0, 1.0),
    )

    straightAngleThreshold: bpy.props.FloatProperty(
        name="Straight angle threshold",
        description=(
            "Threshold for an angle of the building outline: when consider it as straight one. "
            "It may be important for calculation of the longest side of the building outline for a gabled roof."
        ),
        default=175.5,
        min=170.0,
        max=179.95,
        step=10,
    )

    defaultRoofShape: bpy.props.EnumProperty(
        items=(("flat", "flat", "flat shape"), ("gabled", "gabled", "gabled shape")),
        description="Roof shape for a building if the roof shape is not set in OpenStreetMap",
        default="flat",
    )
