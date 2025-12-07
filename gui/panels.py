"""
CashCab Route Import - GUI Panels
Minimal panel definitions for route import functionality only.
"""

import bpy

from ..asset_manager import AssetRegistry, AssetType


ROUTE_PANEL_UI_VERSION = "2.2.0"
ROUTE_PANEL_LABEL = f"CashCab ({ROUTE_PANEL_UI_VERSION})"


class BLOSM_UL_DefaultLevels(bpy.types.UIList):
    """UI list for default building levels"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_property):
        row = layout.row()
        row.prop(item, "levels")
        row.prop(item, "weight")


class BLOSM_PT_RouteImport(bpy.types.Panel):
    """Main route import panel with address inputs and fetch button"""

    bl_label = ROUTE_PANEL_LABEL
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CashCab"

    def draw(self, context):
        layout = self.layout
        addon = context.scene.blosm

        # Address inputs
        col = layout.column(align=True)
        col.prop(addon, "route_start_address", text="Start Address")

        # Waypoints section
        waypoints_box = layout.box()
        waypoints_box.label(text="Waypoints (Optional)", icon='CURVE_PATH')
        for idx, waypoint in enumerate(addon.route_waypoints):
            row = waypoints_box.row(align=True)
            row.prop(waypoint, "address", text=f"{idx+1}")
            row.operator("blosm.remove_waypoint", text="", icon='X').index = idx
        waypoints_box.operator("blosm.add_waypoint", text="Add Stop", icon='ADD')

        col = layout.column(align=True)
        col.prop(addon, "route_end_address", text="End Address")
        layout.prop(addon, "route_padding_m")

        # Import layer toggles
        layer_col = layout.column(align=True)
        layer_col.prop(addon, "route_import_roads", text="Import Roads")
        layer_col.prop(addon, "route_import_buildings", text="Import Buildings")
        layer_col.prop(addon, "route_create_preview_animation", text="Create Animated Route & Assets")

        # Minimal RouteCam toggle (keeps advanced UI hidden)
        layer_col.prop(addon, "route_enable_routecam", text="Enable RouteCam Camera")

        # City extension controls (always visible so feature is discoverable)
        extend_box = layout.box()
        extend_box.label(text="Extend City", icon='ARROW_LEFTRIGHT')
        extend_box.label(text="Tiles are ~1.4 km; raise distance if no tiles change.", icon='INFO')

        # Disable controls until a prior import stored the import bbox
        scene = context.scene
        bbox = scene.get("blosm_import_bbox") if scene else None
        has_import_state = False
        if bbox is not None:
            try:
                # ID properties may come back as a Blender array type; just
                # verify we have 4 numeric entries instead of strict types.
                has_import_state = len(bbox) == 4
            except Exception:
                has_import_state = False

        row = extend_box.row()
        row.enabled = has_import_state
        row.prop(addon, "route_extend_m", text="Extend by (m)")

        row = extend_box.row()
        row.enabled = has_import_state
        row.operator("blosm.extend_city_area", text="Extend City (delta tiles only)", icon='ADD')

        if not has_import_state:
            extend_box.label(text="Run Fetch Route and Map first to enable extend.", icon='INFO')

        # Animation settings - grouped in a collapsible tab-like box
        anim_box = layout.box()
        header = anim_box.row()
        header.prop(addon, "ui_show_animation", text="", icon='TRIA_DOWN' if addon.ui_show_animation else 'TRIA_RIGHT', emboss=False)
        header.label(text="Animation Controls", icon='TIME')

        if addon.ui_show_animation:
            # Car animation
            car_col = anim_box.column(align=True)
            car_col.label(text="Car Animation:", icon='AUTO')
            car_col.prop(context.scene, "blosm_anim_start", text="Start Frame")
            car_col.prop(context.scene, "blosm_anim_end", text="End Frame")
            car_col.prop(context.scene, "blosm_lead_frames", text="Lead Frames")

            anim_box.separator()

            # Route trace animation
            route_col = anim_box.column(align=True)
            route_col.label(text="Route Trace (GeoNodes):", icon='CURVE_PATH')
            route_col.prop(context.scene, "blosm_route_start", text="Start Frame")
            route_col.prop(context.scene, "blosm_route_end", text="End Frame")

            anim_box.separator()

            # Free driver variables (not wired; for use in your own drivers)
            extra_col = anim_box.column(align=True)
            extra_col.label(text="Custom Variables:", icon='DRIVER')
            extra_col.prop(context.scene, "blosm_base_start", text="Base_Start")
            extra_col.prop(context.scene, "blosm_base_end", text="Base_End")

            anim_box.separator()

        # RouteCam Controls (hidden by default – handled by separate addon)
        if False and addon.route_enable_routecam:
            # Determine target camera: Active Object > Scene Camera
            target_cam = None
            if context.active_object and context.active_object.type == 'CAMERA':
                target_cam = context.active_object
            elif context.scene.camera:
                target_cam = context.scene.camera

            rc_box = anim_box.box()
            rc_box.label(text="RouteCam Director", icon='CAMERA_DATA')
            
            # Batch Settings (Always Visible)
            row = rc_box.row()
            row.prop(addon, "routecam_batch_v2_count")
            row.prop(addon, "routecam_batch_viz_count")

            if target_cam:
                rc_box.label(text=f"Camera: {target_cam.name}", icon='OUTLINER_OB_CAMERA')
                
                # Ensure property group exists
                if hasattr(target_cam, 'routecam_unified'):
                    s = target_cam.routecam_unified
                    
                    # Engine Select
                    row = rc_box.row()
                    row.prop(s, "engine_mode", expand=True)
                    
                    rc_box.prop(s, "target_curve")
                    rc_box.prop(s, "duration")

                    # Dynamic UI
                    if s.engine_mode == 'V2':
                        v2_col = rc_box.column(align=True)
                        v2_col.prop(s, "margin")
                        v2_col.prop(s, "zoom_ratio")
                        
                        row = v2_col.row(align=True)
                        row.prop(s, "pitch_start")
                        row.prop(s, "pitch_end")
                        
                        v2_col.prop(s, "yaw_offset")
                        
                        row = v2_col.row(align=True)
                        row.prop(s, "beat_drift")
                        row.prop(s, "beat_zoom")
                        
                        op_row = rc_box.row(align=True)
                        op_row.operator("routecam.generate", text="Analyze", icon='FILE_REFRESH')
                        if s.v2_cached_plan:
                            op_row.operator("routecam.bake_v2", text="Bake", icon='ACTION')
                            
                    elif s.engine_mode == 'VIZ':
                        viz_col = rc_box.column(align=True)
                        viz_col.prop(s, "sect1_margin")
                        viz_col.prop(s, "sect1_angle")
                        viz_col.prop(s, "sect2_time")
                        viz_col.prop(s, "sect2_push")
                        
                        rc_box.operator("routecam.generate", text="Generate (Direct Bake)", icon='FILE_REFRESH')
                else:
                    rc_box.label(text="RouteCam properties missing", icon='ERROR')
            else:
                rc_box.label(text="No Camera Selected", icon='INFO')
                rc_box.operator("object.camera_add", text="Create Camera", icon='ADD')

        # Main action buttons
        layout.separator()
        layout.operator("blosm.fetch_route_map", text="Fetch Route & Map", icon='IMPORT')
        layout.operator("blosm.clean_and_clear", text="Clean & Clear", icon='TRASH')


class BLOSM_PT_RouteImportAdvanced(bpy.types.Panel):
    """Advanced route import tools"""

    bl_label = "Advanced"
    bl_parent_id = "BLOSM_PT_RouteImport"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CashCab"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        addon = context.scene.blosm

        # Fallback building heights (moved from separate panel)
        layout.separator()
        layout.label(text="Fallback Building Heights", icon='HOME')
        layout.prop(addon, "levelHeight", text="Level Height")

        row = layout.row()
        row.template_list(
            "BLOSM_UL_DefaultLevels", "fallback",
            addon, "defaultLevels",
            addon, "defaultLevelsIndex"
        )
        col = row.column(align=True)
        col.operator("blosm.levels_add", text="", icon='ADD')
        col.operator("blosm.levels_delete", text="", icon='REMOVE')

        # Create Asset section
        layout.separator()
        create_box = layout.box()
        create_box.label(text="Create Asset", icon='FILE_NEW')
        addon = getattr(context.scene, 'blosm', None)
        if addon:
            create_box.prop(addon, "asset_new_id", text="ID")
            create_box.prop(addon, "asset_new_name", text="Name")
            create_box.prop(addon, "asset_new_type", text="Type")
            create_box.prop(addon, "asset_new_datablock", text="Source")
            create_box.prop(addon, "asset_new_blend_path", text="Blend File")
            create_box.prop(addon, "asset_new_collection", text="Collection")
            create_box.operator("blosm.capture_asset", text="Save Asset", icon='FILE_TICK')

        # Manual tools
        layout.separator()
        layout.label(text="Manual Tools (Testing)", icon='MODIFIER')
        layout.operator("blosm.import_assets", text="Import Assets", icon='ASSET_MANAGER')


_ASSET_TYPE_ICONS = {
    AssetType.CAR: 'OUTLINER_OB_EMPTY',
    AssetType.MARKER: 'OUTLINER_OB_EMPTY',
    AssetType.BUILDING: 'MOD_BUILD',
    AssetType.ROAD: 'OUTLINER_OB_CURVE',
    AssetType.MATERIAL: 'MATERIAL',
    AssetType.NODE_GROUP: 'GEOMETRY_NODES',
    AssetType.WORLD: 'WORLD_DATA',
    AssetType.LIGHT: 'LIGHT',
    AssetType.COLLECTION: 'OUTLINER_COLLECTION',
}

_GROUPINGS = [
    ("Objects", 'OBJECT_DATAMODE', {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}),
    ("Geometry Nodes", 'GEOMETRY_NODES', {AssetType.NODE_GROUP}),
    ("Materials & Shaders", 'MATERIAL', {AssetType.MATERIAL}),
    ("World & Collections", 'WORLD_DATA', {AssetType.WORLD, AssetType.COLLECTION}),
]


class BLOSM_PT_AssetManager(bpy.types.Panel):
    """Asset registry browser for quick appending of configured assets."""

    bl_label = "Asset Manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CashCab"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        addon = getattr(context.scene, 'blosm', None)
        if addon:
            layout.prop(addon, "asset_apply_to_selection", toggle=True)
            layout.separator()

        registry = AssetRegistry()
        has_assets = False

        layout.label(text="Registered Assets", icon='ASSET_MANAGER')
        layout.separator(factor=0.5)

        seen_types = set()
        for group_label, group_icon, type_set in _GROUPINGS:
            grouped = []
            for asset_type in type_set:
                assets = registry.get_assets_by_type(asset_type)
                if assets:
                    grouped.append((asset_type, assets))
                    seen_types.add(asset_type)
            if not grouped:
                continue
            has_assets = True

            group_box = layout.box()
            group_box.label(text=group_label, icon=group_icon)

            for asset_type, assets in grouped:
                icon = _ASSET_TYPE_ICONS.get(asset_type, 'DOT')
                group_box.label(text=f"{asset_type.name.replace('_', ' ').title()} ({len(assets)})", icon=icon)
                for asset in assets:
                    row = group_box.row(align=True)
                    is_active = addon and addon.asset_active_id == asset.id
                    if is_active:
                        row.alert = True

                    # Simplified row with fewer icons
                    select_op = row.operator(
                        "blosm.select_registry_asset",
                        text="",
                        icon='PREFERENCES'
                    )
                    select_op.asset_id = asset.id

                    # Asset name as main label
                    name_text = asset.name or asset.id
                    if asset.collection_name:
                        name_text += f" ({asset.collection_name})"
                    row.label(text=name_text)

                    # Action buttons in sub-row
                    action_row = row.row(align=True)
                    action_row.scale_x = 0.8

                    op = action_row.operator(
                        "blosm.spawn_registry_asset",
                        text="",
                        icon='APPEND_BLEND',
                    )
                    op.asset_id = asset.id
                    op.target_collection = asset.collection_name or ""

                    link_op = action_row.operator(
                        "blosm.spawn_registry_asset",
                        text="",
                        icon='LINK_BLEND',
                    )
                    link_op.asset_id = asset.id
                    link_op.target_collection = asset.collection_name or ""
                    link_op.link = True

                    # Add Update Asset button
                    update_op = action_row.operator(
                        "blosm.update_asset_from_scene",
                        text="",
                        icon='FILE_REFRESH'
                    )
                    update_op.asset_id = asset.id

                    if asset.description:
                        desc_row = group_box.row()
                        desc_row.label(text=asset.description, icon='INFO')

        # Handle asset types not mapped to a group
        remaining_types = [atype for atype in AssetType if atype not in seen_types]
        if remaining_types:
            other_box = layout.box()
            other_box.label(text="Other", icon='DOT')
            for asset_type in remaining_types:
                assets = registry.get_assets_by_type(asset_type)
                if not assets:
                    continue
                has_assets = True
                icon = _ASSET_TYPE_ICONS.get(asset_type, 'DOT')
                other_box.label(text=f"{asset_type.name.replace('_', ' ').title()} ({len(assets)})", icon=icon)
                for asset in assets:
                    row = other_box.row(align=True)
                    is_active = addon and addon.asset_active_id == asset.id
                    if is_active:
                        row.alert = True

                    # Simplified row with fewer icons
                    select_op = row.operator(
                        "blosm.select_registry_asset",
                        text="",
                        icon='PREFERENCES'
                    )
                    select_op.asset_id = asset.id

                    # Asset name as main label
                    name_text = asset.name or asset.id
                    if asset.collection_name:
                        name_text += f" ({asset.collection_name})"
                    row.label(text=name_text)

                    # Action buttons in sub-row
                    action_row = row.row(align=True)
                    action_row.scale_x = 0.8

                    op = action_row.operator(
                        "blosm.spawn_registry_asset",
                        text="",
                        icon='APPEND_BLEND',
                    )
                    op.asset_id = asset.id
                    op.target_collection = asset.collection_name or ""

                    link_op = action_row.operator(
                        "blosm.spawn_registry_asset",
                        text="",
                        icon='LINK_BLEND',
                    )
                    link_op.asset_id = asset.id
                    link_op.target_collection = asset.collection_name or ""
                    link_op.link = True

                    # Add Update Asset button
                    update_op = action_row.operator(
                        "blosm.update_asset_from_scene",
                        text="",
                        icon='FILE_REFRESH'
                    )
                    update_op.asset_id = asset.id

        if not has_assets:
            layout.label(text="No assets defined in registry", icon='ERROR')

        if addon and addon.asset_active_id:
            active_asset = registry.get_asset(addon.asset_active_id)
            if active_asset:
                edit_box = layout.box()
                edit_box.label(text=f"Edit Asset: {active_asset.id}", icon='SETTINGS')
                edit_box.prop(addon, "asset_edit_name")
                edit_box.prop(addon, "asset_edit_description")
                edit_box.prop(addon, "asset_edit_blend_path")
                edit_box.prop(addon, "asset_edit_datablock")
                edit_box.prop(addon, "asset_edit_collection")
                edit_box.prop(addon, "asset_edit_tags")

                object_types = {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}
                if active_asset.type in object_types:
                    edit_box.prop(addon, "asset_edit_location")
                    edit_box.prop(addon, "asset_edit_rotation")
                    edit_box.prop(addon, "asset_edit_scale")
                else:
                    edit_box.label(text="Transforms not applicable for this asset type", icon='INFO')

                # Save and Cancel buttons
                button_row = edit_box.row()
                save_op = button_row.operator("blosm.update_registry_asset", text="Save Changes", icon='FILE_TICK')
                cancel_op = button_row.operator("blosm.cancel_asset_edit", text="Cancel", icon='X')
            else:
                layout.label(text="Active asset not found in registry", icon='ERROR')


# FallbackHeights panel removed - now integrated into Advanced panel


