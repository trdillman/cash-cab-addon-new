"""
BLOSM Route Import - GUI Operators - FIXED

Extended with asset manager helpers for appending assets and capturing new ones.
UPDATED to use the new Dict-based asset isolation interface.
"""

import shutil
from pathlib import Path

import bpy

from ..asset_manager import (
    AssetRegistry,
    spawn_asset_by_id,
    AssetType,
    AssetDefinition,
    TransformData,
    registry as global_asset_registry,
)

from ..asset_manager.asset_safety import AssetSafety
from ..asset_manager.simple_asset_updater import SimpleAssetUpdater


class BLOSM_OT_AddWaypoint(bpy.types.Operator):
    """Add a waypoint stop to the route"""

    bl_idname = "blosm.add_waypoint"
    bl_label = "Add Waypoint"
    bl_description = "Add an intermediate stop between start and end"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        context.scene.blosm.route_waypoints.add()
        return {'FINISHED'}


class BLOSM_OT_RemoveWaypoint(bpy.types.Operator):
    """Remove a waypoint stop from the route"""

    bl_idname = "blosm.remove_waypoint"
    bl_label = "Remove Waypoint"
    bl_description = "Remove this waypoint stop"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        waypoints = context.scene.blosm.route_waypoints
        if 0 <= self.index < len(waypoints):
            waypoints.remove(self.index)
        return {'FINISHED'}


class BLOSM_OT_LevelsAdd(bpy.types.Operator):
    """Add an entry for default building levels"""

    bl_idname = "blosm.levels_add"
    bl_label = "+"
    bl_description = "Add an entry for the default number of levels. " +\
        "Enter both the number of levels and its relative weight between 1 and 100"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        context.scene.blosm.defaultLevels.add()
        return {'FINISHED'}


class BLOSM_OT_LevelsDelete(bpy.types.Operator):
    """Delete an entry from default building levels"""

    bl_idname = "blosm.levels_delete"
    bl_label = "-"
    bl_description = "Delete the selected entry for the default number of levels"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.blosm.defaultLevels) > 1

    def invoke(self, context, event):
        addon = context.scene.blosm
        defaultLevels = addon.defaultLevels
        defaultLevels.remove(addon.defaultLevelsIndex)
        if addon.defaultLevelsIndex >= len(defaultLevels):
            addon.defaultLevelsIndex = 0
        return {'FINISHED'}


class BLOSM_OT_CaptureAsset(bpy.types.Operator):
    """Capture the current selection into the asset registry."""

    bl_idname = "blosm.capture_asset"
    bl_label = "Save Asset"
    bl_description = "Create or update an asset entry using the current selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon = getattr(getattr(context, 'scene', None), 'blosm', None)
        if addon is None:
            self.report({'ERROR'}, "CashCab properties are unavailable in this context")
            return {'CANCELLED'}

        asset_id = addon.asset_new_id.strip()
        if not asset_id:
            self.report({'ERROR'}, "Asset ID is required")
            return {'CANCELLED'}

        name = addon.asset_new_name.strip() or asset_id

        try:
            asset_type = AssetType(addon.asset_new_type)
        except ValueError:
            self.report({'ERROR'}, "Unsupported asset type selected")
            return {'CANCELLED'}

        datablock_key = addon.asset_new_datablock_storage or addon.asset_new_datablock
        if not datablock_key or datablock_key == "__NONE__":
            self.report({'ERROR'}, "No source datablock available for the selected type")
            return {'CANCELLED'}

        datablock = self._resolve_datablock(asset_type, datablock_key)
        if datablock is None:
            self.report({'ERROR'}, f"Datablock '{datablock_key}' could not be found")
            return {'CANCELLED'}

        blend_path_input = addon.asset_new_blend_path.strip()
        if not blend_path_input:
            self.report({'ERROR'}, "Blend file path is required")
            return {'CANCELLED'}

        blend_path_resolved = Path(bpy.path.abspath(blend_path_input))

        registry = AssetRegistry()
        base_dir = registry.config_path.parent

        if blend_path_resolved.exists():
            try:
                blend_file = blend_path_resolved.relative_to(base_dir).as_posix()
            except ValueError:
                blend_file = blend_path_resolved.as_posix()
        else:
            blend_file = blend_path_resolved.as_posix()

        transform = TransformData()
        object_types = {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}
        if asset_type in object_types and isinstance(datablock, bpy.types.Object):
            transform = TransformData(
                location=tuple(float(v) for v in datablock.location),
                rotation_euler=tuple(float(v) for v in datablock.rotation_euler),
                scale=tuple(float(v) for v in datablock.scale),
            )

        collection_name = addon.asset_new_collection.strip() or None
        if collection_name is None and isinstance(datablock, bpy.types.Object):
            collections = getattr(datablock, 'users_collection', None)
            if collections:
                collection_name = collections[0].name

        asset_definition = AssetDefinition(
            id=asset_id,
            name=name,
            type=asset_type,
            blend_file=blend_file,
            datablock_name=datablock_key,
            default_transform=transform,
            category=asset_type.value,
            description="",
            version="1.0.0",
            tags=[],
            collection_name=collection_name,
            hide_viewport=False,
            hide_render=False,
            properties={},
        )

        registry.register_asset(asset_definition)
        registry.save()
        try:
            global_asset_registry.load()
        except Exception:
            pass

        addon.asset_new_id = ""
        addon.asset_new_name = ""
        addon.asset_new_collection = ""
        addon.asset_new_datablock_storage = "__NONE__"

        self.report({'INFO'}, f"Asset '{asset_id}' saved to registry")
        return {'FINISHED'}

    @staticmethod
    def _resolve_datablock(asset_type: AssetType, key: str):
        if asset_type in {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}:
            return bpy.data.objects.get(key)
        if asset_type == AssetType.MATERIAL:
            return bpy.data.materials.get(key)
        if asset_type == AssetType.NODE_GROUP:
            return bpy.data.node_groups.get(key)
        if asset_type == AssetType.WORLD:
            return bpy.data.worlds.get(key)
        if asset_type == AssetType.COLLECTION:
            return bpy.data.collections.get(key)
        return None


class BLOSM_OT_SelectRegistryAsset(bpy.types.Operator):
    """Select an asset for editing in the panel."""

    bl_idname = "blosm.select_registry_asset"
    bl_label = "Select Asset"
    bl_description = "Load asset details into the editor"

    asset_id: bpy.props.StringProperty()

    def execute(self, context):
        addon = getattr(getattr(context, 'scene', None), 'blosm', None)
        if addon is None:
            self.report({'ERROR'}, "CashCab properties are unavailable")
            return {'CANCELLED'}

        registry = AssetRegistry()
        asset = registry.get_asset(self.asset_id)
        if asset is None:
            self.report({'ERROR'}, f"Asset '{self.asset_id}' not found in registry")
            return {'CANCELLED'}

        addon.asset_active_id = asset.id
        addon.asset_edit_name = asset.name
        addon.asset_edit_description = asset.description or ""

        blend_abs = (registry.config_path.parent / asset.blend_file).resolve()
        addon.asset_edit_blend_path = blend_abs.as_posix()

        addon.asset_edit_datablock = asset.datablock_name
        addon.asset_edit_collection = asset.collection_name or ""
        addon.asset_edit_tags = ", ".join(asset.tags) if asset.tags else ""

        object_types = {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}
        if asset.type in object_types:
            addon.asset_edit_location = asset.default_transform.location
            addon.asset_edit_rotation = asset.default_transform.rotation_euler
            addon.asset_edit_scale = asset.default_transform.scale
        else:
            addon.asset_edit_location = (0.0, 0.0, 0.0)
            addon.asset_edit_rotation = (0.0, 0.0, 0.0)
            addon.asset_edit_scale = (1.0, 1.0, 1.0)

        self.report({'INFO'}, f"Editing asset '{asset.id}'")
        return {'FINISHED'}


class BLOSM_OT_UpdateRegistryAsset(bpy.types.Operator):
    """Update the selected asset's metadata in the registry."""

    bl_idname = "blosm.update_registry_asset"
    bl_label = "Save Asset Changes"
    bl_description = "Write modified parameters back to the asset registry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon = getattr(getattr(context, 'scene', None), 'blosm', None)
        if addon is None:
            self.report({'ERROR'}, "CashCab properties are unavailable")
            return {'CANCELLED'}

        asset_id = addon.asset_active_id.strip()
        if not asset_id:
            self.report({'ERROR'}, "No active asset selected")
            return {'CANCELLED'}

        registry = AssetRegistry()
        asset = registry.get_asset(asset_id)
        if asset is None:
            self.report({'ERROR'}, f"Asset '{asset_id}' not found in registry")
            return {'CANCELLED'}

        name = addon.asset_edit_name.strip() or asset_id
        description = addon.asset_edit_description.strip()
        blend_path_input = addon.asset_edit_blend_path.strip() or asset.blend_file

        blend_path_resolved = Path(bpy.path.abspath(blend_path_input))
        base_dir = registry.config_path.parent
        if blend_path_resolved.exists():
            try:
                blend_file = blend_path_resolved.relative_to(base_dir).as_posix()
            except ValueError:
                blend_file = blend_path_resolved.as_posix()
        else:
            blend_file = blend_path_input

        datablock_name = addon.asset_edit_datablock.strip() or asset.datablock_name
        collection_name = addon.asset_edit_collection.strip() or None
        tags = [tag.strip() for tag in addon.asset_edit_tags.split(',') if tag.strip()]

        default_transform = asset.default_transform
        object_types = {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}
        if asset.type in object_types:
            default_transform = TransformData(
                location=tuple(float(v) for v in addon.asset_edit_location),
                rotation_euler=tuple(float(v) for v in addon.asset_edit_rotation),
                scale=tuple(float(v) for v in addon.asset_edit_scale),
            )

        updated = AssetDefinition(
            id=asset.id,
            name=name,
            type=asset.type,
            blend_file=blend_file,
            datablock_name=datablock_name,
            default_transform=default_transform,
            category=asset.category,
            description=description,
            version=asset.version,
            tags=tags,
            collection_name=collection_name,
            hide_viewport=asset.hide_viewport,
            hide_render=asset.hide_render,
            properties=asset.properties,
        )

        registry.register_asset(updated)
        registry.save()
        try:
            global_asset_registry.load()
        except Exception:
            pass

        addon.asset_active_id = updated.id
        self.report({'INFO'}, f"Asset '{updated.id}' updated")
        return {'FINISHED'}


class BLOSM_OT_UpdateAssetFromScene(bpy.types.Operator):
    """Update a registered asset using current Blender selection."""

    bl_idname = "blosm.update_asset_from_scene"
    bl_label = "Update Asset"
    bl_description = "Replace registered asset with currently selected object/material/world/etc."
    bl_options = {'REGISTER', 'UNDO'}

    asset_id: bpy.props.StringProperty(name="Asset ID")

    def execute(self, context):
        registry = AssetRegistry()
        asset = registry.get_asset(self.asset_id)
        if not asset:
            self.report({'ERROR'}, f"Asset '{self.asset_id}' not found in registry")
            return {'CANCELLED'}

        try:
            success = self._update_asset_from_scene(context, asset, registry)
            if success:
                # Reload global registry to update UI
                global_asset_registry.load()
                self.report({'INFO'}, f"Asset '{self.asset_id}' updated from scene")
            else:
                self.report({'ERROR'}, f"Failed to update asset '{self.asset_id}'")
                return {'CANCELLED'}
        except Exception as exc:
            self.report({'ERROR'}, f"Error updating asset '{self.asset_id}': {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}

    def _update_asset_from_scene(self, context, asset, registry):
        """Update asset file based on asset type and current selection"""

        # Get current selection
        selection = context.selected_objects

        if not selection and asset.type in {AssetType.CAR, AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}:
            self.report({'ERROR'}, f"Please select an object to update {asset.id}")
            return False

        # Update based on asset type
        if asset.type == AssetType.CAR:
            return self._update_object_asset(asset, selection, registry)
        elif asset.type == AssetType.MATERIAL:
            return self._update_material_asset(asset, context, registry)
        elif asset.type == AssetType.WORLD:
            return self._update_world_asset(asset, context, registry)
        elif asset.type == AssetType.NODE_GROUP:
            return self._update_node_group_asset(asset, registry)
        elif asset.type == AssetType.COLLECTION:
            return self._update_collection_asset(asset, selection, registry)
        else:
            # Handle other object types generically
            if asset.type in {AssetType.MARKER, AssetType.BUILDING, AssetType.ROAD, AssetType.LIGHT}:
                return self._update_object_asset(asset, selection, registry)
            return False

    def _update_object_asset(self, asset, selection, registry):
        """Update object-based asset using simple, safe approach"""
        # Use first selected object with proper validation
        if not selection or len(selection) == 0:
            self.report({'ERROR'}, f"No object selected to update {asset.id}")
            return False

        obj = selection[0]

        # Validate object is valid and has required attributes
        if not obj or not hasattr(obj, 'name') or not obj.name:
            self.report({'ERROR'}, f"Invalid object selected for {asset.id}")
            return False

        try:
            # DEBUG: Log permission and path information
            import tempfile
            from pathlib import Path

            # Check current working directory and permissions
            current_dir = Path.cwd()
            print(f"[DEBUG] Current working directory: {current_dir}")

            # Determine where assets will be saved
            with AssetSafety() as safety:
                print(f"[DEBUG] Assets directory: {safety.assets_dir}")
                print(f"[DEBUG] Target asset file: {safety.assets_dir / asset.blend_file}")

                # Test write permissions
                test_file = safety.assets_dir / "permission_test.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    print(f"[DEBUG] Write permissions: OK for {safety.assets_dir}")
                except Exception as perm_e:
                    print(f"[DEBUG] Write permissions FAILED: {perm_e}")
                    self.report({'ERROR'}, f"Permission denied writing to {safety.assets_dir}: {perm_e}")
                    return False

            # Use the safe asset update system
            with AssetSafety() as safety:
                print(f"[DEBUG] Starting asset update for {asset.id} using object {obj.name}")
                success = safety.safe_update_object_asset(asset.id, obj, f"GUI update from {obj.name}")
                print(f"[DEBUG] AssetSafety result: {success}")

                if not success:
                    self.report({'ERROR'}, f"Failed to safely update asset {asset.id} - check console for details")
                    return False

            # Update transform data safely - validate object still exists and has required attributes
            if obj and hasattr(obj, 'location') and hasattr(obj, 'rotation_euler') and hasattr(obj, 'scale'):
                try:
                    new_transform = TransformData(
                        location=tuple(float(v) for v in obj.location),
                        rotation_euler=tuple(float(v) for v in obj.rotation_euler),
                        scale=tuple(float(v) for v in obj.scale),
                    )
                except (AttributeError, TypeError, ValueError) as e:
                    print(f"Warning: Could not capture transform data for {obj.name}: {e}")
                    # Use existing transform data as fallback
                    new_transform = asset.default_transform
            else:
                # Object may have been deleted during update, use existing transform
                new_transform = asset.default_transform

            # Update asset definition with new name and transform
            updated_asset = AssetDefinition(
                id=asset.id,
                name=asset.name,
                type=asset.type,
                blend_file=asset.blend_file,
                datablock_name=obj.name if obj and hasattr(obj, 'name') else asset.datablock_name,
                default_transform=new_transform,
                category=asset.category,
                description=asset.description,
                version=asset.version,
                tags=asset.tags,
                collection_name=asset.collection_name,
                hide_viewport=asset.hide_viewport,
                hide_render=asset.hide_render,
                properties=asset.properties,
            )

            registry.register_asset(updated_asset)
            registry.save()
            return True

        except Exception as exc:
            print(f"Failed to update object asset: {exc}")
            self.report({'ERROR'}, f"Failed to update object asset: {exc}")
            return False

    def _update_material_asset(self, asset, context, registry):
        """Update material-based asset using simple, safe approach"""
        # Get selected object's active material with proper validation
        active_obj = context.active_object
        if not active_obj or not active_obj.active_material:
            self.report({'ERROR'}, f"Please select an object with a material to update {asset.id}")
            return False

        material = active_obj.active_material

        # Validate material is valid and has required attributes
        if not material or not hasattr(material, 'name') or not material.name:
            self.report({'ERROR'}, f"Invalid material selected for {asset.id}")
            return False

        try:
            # Use the safe asset update system
            with AssetSafety() as safety:
                success = safety.safe_update_material_asset(asset.id, material, f"GUI update from {material.name}")

                if not success:
                    self.report({'ERROR'}, f"Failed to safely update material asset {asset.id}")
                    return False

            # Update asset definition with material name
            updated_asset = AssetDefinition(
                id=asset.id,
                name=asset.name,
                type=asset.type,
                blend_file=asset.blend_file,
                datablock_name=material.name if material and hasattr(material, 'name') else asset.datablock_name,
                default_transform=asset.default_transform,
                category=asset.category,
                description=asset.description,
                version=asset.version,
                tags=asset.tags,
                collection_name=asset.collection_name,
                hide_viewport=asset.hide_viewport,
                hide_render=asset.hide_render,
                properties=asset.properties,
            )

            registry.register_asset(updated_asset)
            registry.save()
            return True

        except Exception as exc:
            print(f"Failed to update material asset: {exc}")
            self.report({'ERROR'}, f"Failed to update material asset: {exc}")
            return False

    def _update_world_asset(self, asset, context, registry):
        """Update world-based asset using simplified system"""
        world = context.scene.world
        if not world:
            self.report({'ERROR'}, f"No active world to update {asset.id}")
            return False

        try:
            # Use the safe asset update system
            with AssetSafety() as safety:
                success = safety.safe_update_world_asset(asset.id, world, f"GUI update from {world.name}")

                if not success:
                    self.report({'ERROR'}, f"Failed to safely update world asset {asset.id}")
                    return False

            # Update asset definition with world name
            updated_asset = AssetDefinition(
                id=asset.id,
                name=asset.name,
                type=asset.type,
                blend_file=asset.blend_file,
                datablock_name=world.name if world and hasattr(world, 'name') else asset.datablock_name,
                default_transform=asset.default_transform,
                category=asset.category,
                description=asset.description,
                version=asset.version,
                tags=asset.tags,
                collection_name=asset.collection_name,
                hide_viewport=asset.hide_viewport,
                hide_render=asset.hide_render,
                properties=asset.properties,
            )

            registry.register_asset(updated_asset)
            registry.save()
            return True

        except Exception as exc:
            print(f"Failed to update world asset: {exc}")
            self.report({'ERROR'}, f"Failed to update world asset: {exc}")
            return False

    def _update_node_group_asset(self, asset, registry):
        """Update node group asset using simplified system"""
        # Find the node group from registry
        node_group = bpy.data.node_groups.get(asset.datablock_name)
        if not node_group:
            self.report({'ERROR'}, f"Node group '{asset.datablock_name}' not found")
            return False

        try:
            # Use the safe asset update system
            with AssetSafety() as safety:
                success = safety.safe_update_nodegroup_asset(asset.id, node_group, f"GUI update from {node_group.name}")

                if not success:
                    self.report({'ERROR'}, f"Failed to safely update node group asset {asset.id}")
                    return False

            # Update asset definition with node group name
            updated_asset = AssetDefinition(
                id=asset.id,
                name=asset.name,
                type=asset.type,
                blend_file=asset.blend_file,
                datablock_name=node_group.name if node_group and hasattr(node_group, 'name') else asset.datablock_name,
                default_transform=asset.default_transform,
                category=asset.category,
                description=asset.description,
                version=asset.version,
                tags=asset.tags,
                collection_name=asset.collection_name,
                hide_viewport=asset.hide_viewport,
                hide_render=asset.hide_render,
                properties=asset.properties,
            )

            registry.register_asset(updated_asset)
            registry.save()
            return True

        except Exception as exc:
            print(f"Failed to update node group asset: {exc}")
            self.report({'ERROR'}, f"Failed to update node group asset: {exc}")
            return False

    def _update_collection_asset(self, asset, selection, registry):
        """Update collection-based asset using simplified system"""
        # Save entire selected collection
        if not selection:
            self.report({'ERROR'}, f"Please select objects in collection to update {asset.id}")
            return False

        # Get all collections containing selected objects
        collections = set()
        for obj in selection:
            for coll in obj.users_collection:
                collections.add(coll)

        if not collections:
            self.report({'ERROR'}, f"No collection found for updating {asset.id}")
            return False

        try:
            # Use the safe asset update system
            with AssetSafety() as safety:
                success = safety.safe_update_collection_asset(asset.id, list(collections), f"GUI update from collection")

                if not success:
                    self.report({'ERROR'}, f"Failed to safely update collection asset {asset.id}")
                    return False

            # Update asset definition with collection name
            first_collection = list(collections)[0]
            updated_asset = AssetDefinition(
                id=asset.id,
                name=asset.name,
                type=asset.type,
                blend_file=asset.blend_file,
                datablock_name=first_collection.name if first_collection and hasattr(first_collection, 'name') else asset.datablock_name,
                default_transform=asset.default_transform,
                category=asset.category,
                description=asset.description,
                version=asset.version,
                tags=asset.tags,
                collection_name=first_collection.name if first_collection and hasattr(first_collection, 'name') else asset.collection_name,
                hide_viewport=asset.hide_viewport,
                hide_render=asset.hide_render,
                properties=asset.properties,
            )

            registry.register_asset(updated_asset)
            registry.save()
            return True

        except Exception as exc:
            print(f"Failed to update collection asset: {exc}")
            self.report({'ERROR'}, f"Failed to update collection asset: {exc}")
            return False


class BLOSM_OT_SpawnRegistryAsset(bpy.types.Operator):
    """Append or link an asset defined in the BLOSM registry."""

    bl_idname = "blosm.spawn_registry_asset"
    bl_label = "Add Asset"
    bl_description = "Append or link the selected asset from the registry"
    bl_options = {'REGISTER', 'UNDO'}

    asset_id: bpy.props.StringProperty(name="Asset ID")
    link: bpy.props.BoolProperty(
        name="Link",
        description="Link the datablock instead of appending",
        default=False,
    )
    target_collection: bpy.props.StringProperty(
        name="Target Collection",
        description="Collection to place appended objects into",
        default="",
    )

    def execute(self, context):
        registry = AssetRegistry()
        collection_name = self.target_collection.strip() or None
        asset = registry.get_asset(self.asset_id)
        if not asset:
            self.report({'ERROR'}, f"Asset '{self.asset_id}' not found in registry")
            return {'CANCELLED'}
        try:
            created = spawn_asset_by_id(
                self.asset_id,
                registry=registry,
                link=self.link,
                collection_name=collection_name,
            )
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to load asset '{self.asset_id}': {exc}")
            return {'CANCELLED'}

        summary = []

        # Select first created object for convenience
        if created:
            first = created[0]
            if hasattr(first, 'select_set'):
                for obj in context.selected_objects:
                    try:
                        obj.select_set(False)
                    except Exception:
                        pass
                try:
                    first.select_set(True)
                    context.view_layer.objects.active = first
                except Exception:
                    pass

        # Optionally apply non-object assets to active selection
        apply_to_selection = False
        try:
            apply_to_selection = bool(context.scene.blosm.asset_apply_to_selection)
        except Exception:
            apply_to_selection = False

        if apply_to_selection and asset.type == AssetType.MATERIAL:
            active = context.view_layer.objects.active if context.view_layer else None
            if active and hasattr(active, 'data') and hasattr(active.data, 'materials'):
                target_mat = created[0] if created else asset.datablock_name
                material = None
                if isinstance(target_mat, bpy.types.Material):  # type: ignore[attr-defined]
                    material = target_mat
                else:
                    material = bpy.data.materials.get(asset.datablock_name)
                if material:
                    if active.data.materials:
                        active.data.materials[0] = material
                    else:
                        active.data.materials.append(material)
                    summary.append(f"assigned material '{material.name}' to '{active.name}'")
                else:
                    summary.append("material not found after append")

        if apply_to_selection and asset.type == AssetType.NODE_GROUP:
            active = context.view_layer.objects.active if context.view_layer else None
            node_group = bpy.data.node_groups.get(asset.datablock_name)
            if active and node_group:
                modifier = None
                for mod in active.modifiers:
                    if mod.type == 'NODES':
                        modifier = mod
                        break
                if modifier is None:
                    modifier = active.modifiers.new(name=node_group.name, type='NODES')
                modifier.node_group = node_group
                summary.append(f"assigned node group '{node_group.name}' to '{active.name}'")

        if apply_to_selection and asset.type == AssetType.WORLD:
            world = bpy.data.worlds.get(asset.datablock_name)
            scene = getattr(context, 'scene', None)
            if world and scene:
                scene.world = world
                summary.append(f"set scene world to '{world.name}'")

        if not summary:
            target_descr = asset.type.name.lower().replace('_', ' ')
            summary.append(f"made {target_descr} available")

        self.report({'INFO'}, f"Asset '{self.asset_id}': {', '.join(summary)}")
        return {'FINISHED'}