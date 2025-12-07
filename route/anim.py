"""Route animation driver helpers."""


from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import bpy
from mathutils import Matrix, Vector

from . import assets as route_assets
from . import nodes as route_nodes
from . import resolve as route_resolve
from .config import DEFAULT_CONFIG

# Constants from configuration
ROUTE_MODIFIER_NAME = route_nodes.ROUTE_MODIFIER_NAME
LEAD_OBJECT_NAME = DEFAULT_CONFIG.objects.lead_object_name
CAR_CONSTRAINT_NAME = DEFAULT_CONFIG.objects.car_constraint_name
LEAD_CONSTRAINT_NAME = DEFAULT_CONFIG.objects.lead_constraint_name
DAMPED_TRACK_NAME = DEFAULT_CONFIG.objects.damped_track_name
_DEFAULT_FLOAT_NAME = DEFAULT_CONFIG.animation.gn_offset_factor_socket
_START_OBJECT_NAME = DEFAULT_CONFIG.objects.start_marker_name

def _smoothstep(value: float) -> float:
    """Smoothstep function for keyframe interpolation."""
    value = float(value)
    if value < 0.0:
        value = 0.0
    elif value > 1.0:
        value = 1.0
    return value * value * (3.0 - 2.0 * value)


def _remove_existing_keyframes(id_data: Optional[bpy.types.ID], data_path: str) -> None:
    """Remove all existing keyframes for a given data path."""
    if not id_data:
        return
    animation_data = getattr(id_data, 'animation_data', None)
    if not animation_data:
        return
    action = animation_data.action
    if not action:
        return

    # Find and remove all fcurves for this data path
    for fcurve in list(action.fcurves):
        if fcurve.data_path == data_path:
            action.fcurves.remove(fcurve)


def _create_animation_keyframes(
    id_data: Optional[bpy.types.ID],
    data_path: str,
    start_frame: int,
    end_frame: int,
    lead_frames: int = 0,
    *,
    start_value: float = 0.0,
    end_value: float = 1.0,
    use_lead: bool = False,
) -> bool:
    """Create keyframes for animation using Blender's bezier interpolation.

    Args:
        id_data: Object to animate
        data_path: Property path to animate
        start_frame: Start frame for animation
        end_frame: End frame for animation
        lead_frames: Unused (kept for backward compatibility)
        use_lead: Unused (lead timing is handled via values, not frame offsets)

    Returns:
        True if keyframes were created successfully
    """
    if not id_data or end_frame <= start_frame:
        return False

    try:
        # Ensure animation data exists
        id_data.animation_data_create()
    except Exception:
        return False

    # Remove existing keyframes
    _remove_existing_keyframes(id_data, data_path)

    # Create action if needed
    if not id_data.animation_data.action:
        id_data.animation_data.action = bpy.data.actions.new(f"{id_data.name}_action")

    # Use the same frame range for car and lead so timing stays aligned.
    # Lead/lag behavior is expressed by slightly offset start/end *values*,
    # not by shifting the frame range.
    actual_start = start_frame

    # Set start value (0.0) and end value (1.0) using direct constraint access
    try:
        # Extract constraint and property from data_path
        if data_path.startswith('constraints["') and '"]' in data_path:
            constraint_name = data_path.split('"')[1]
            property_name = data_path.split('.')[-1]

            # Find the constraint by name
            target_constraint = None
            for constraint in id_data.constraints:
                if constraint.name == constraint_name:
                    target_constraint = constraint
                    break

            if target_constraint and hasattr(target_constraint, property_name):
                # Set start value
                setattr(target_constraint, property_name, start_value)
                id_data.keyframe_insert(data_path=data_path, frame=actual_start)

                # Set end value
                setattr(target_constraint, property_name, end_value)
                id_data.keyframe_insert(data_path=data_path, frame=end_frame)
            else:
                print(f"[BLOSM] Cannot access constraint property: {data_path}")
                return False
        else:
            print(f"[BLOSM] Invalid data path format: {data_path}")
            return False
    except Exception as e:
        print(f"[BLOSM] Error setting keyframe values: {e}")
        return False

    # Get the created fcurve and set interpolation to bezier
    animation_data = getattr(id_data, 'animation_data', None)
    if animation_data and animation_data.action:
        for fcurve in animation_data.action.fcurves:
            if fcurve.data_path == data_path and fcurve.array_index == 0:
                # Set interpolation to bezier for smooth curves
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'BEZIER'
                break

    return True




@dataclass(frozen=True)
class DriverSetupResult:
    route: Optional[bpy.types.Object]
    lead_driver: bool
    car_driver: bool
    gn_driver: bool
    lead_constraint: Optional[bpy.types.Constraint]
    car_constraint: Optional[bpy.types.Constraint]
    gn_socket_name: Optional[str]
    lead_follow_ok: bool
    car_follow_ok: bool
    car_damped_ok: bool


def _is_float_socket(socket_type: Optional[str]) -> bool:
    if not socket_type:
        return False
    lowered = socket_type.casefold()
    return "float" in lowered or lowered == "value"


def _matches_socket(socket_type: Optional[str], expected: Optional[str]) -> bool:
    if expected is None:
        return True
    if expected == "FLOAT":
        return _is_float_socket(socket_type)
    if not socket_type:
        return False
    return socket_type.casefold() == expected.casefold()


def _find_gn_input_index(
    node_group: Optional[bpy.types.NodeTree],
    name_or_type: str = "FLOAT",
    prefer_name: str = _DEFAULT_FLOAT_NAME,
) -> Optional[int]:
    if not node_group:
        return None
    fallback_by_name = None
    fallback_by_type = None
    prefer_norm = "".join(ch for ch in (prefer_name or "") if ch.isalnum()).casefold()
    for idx, socket_type, socket_name in route_nodes._iter_group_inputs(node_group):
        name_norm = "".join(ch for ch in (socket_name or "") if ch.isalnum()).casefold()
        if prefer_norm and name_norm == prefer_norm:
            if _matches_socket(socket_type, name_or_type):
                return idx
            if fallback_by_name is None:
                fallback_by_name = idx
        if fallback_by_type is None and _matches_socket(socket_type, name_or_type):
            fallback_by_type = idx
    if fallback_by_type is not None:
        return fallback_by_type
    if fallback_by_name is not None:
        return fallback_by_name
    return None


def _resolve_gn_input_property(
    modifier: Optional[bpy.types.Modifier],
    index: Optional[int],
) -> Optional[str]:
    if modifier is None or index is None:
        return None
    node_group = getattr(modifier, 'node_group', None)
    if not node_group:
        return None
    interface = getattr(node_group, 'interface', None)
    if interface is not None:
        items_tree = getattr(interface, 'items_tree', None)
        if items_tree is not None:
            count = 0
            for item in items_tree:
                if getattr(item, 'item_type', None) == 'SOCKET' and getattr(item, 'in_out', None) == 'INPUT':
                    if count == index:
                        identifier = getattr(item, 'identifier', None)
                        if identifier and identifier in modifier.keys():
                            return identifier
                        break
                    count += 1
    inputs = getattr(node_group, 'inputs', None)
    if inputs and 0 <= index < len(inputs):
        socket = inputs[index]
        identifier = getattr(socket, 'identifier', None)
        if identifier and identifier in modifier.keys():
            return identifier
    candidate = f'Input_{index}'
    if candidate in modifier.keys():
        return candidate
    return None


def _ensure_follow_constraint(obj: Optional[bpy.types.Object], name: str) -> Optional[bpy.types.Constraint]:
    if obj is None:
        return None
    for constraint in obj.constraints:
        if constraint.type == 'FOLLOW_PATH' and constraint.name == name:
            return constraint
    try:
        constraint = obj.constraints.new('FOLLOW_PATH')
    except Exception:
        return None
    constraint.name = name
    return constraint


def _configure_follow_path(constraint: Optional[bpy.types.Constraint], target: Optional[bpy.types.Object]) -> None:
    if constraint is None:
        return
    constraint.target = target
    if hasattr(constraint, 'use_curve_follow'):
        constraint.use_curve_follow = True
    if hasattr(constraint, 'use_fixed_position'):
        constraint.use_fixed_position = True
    if hasattr(constraint, 'use_fixed_location'):
        constraint.use_fixed_location = True
    if hasattr(constraint, 'forward_axis'):
        constraint.forward_axis = 'FORWARD_X'
    if hasattr(constraint, 'up_axis'):
        constraint.up_axis = 'UP_Z'

def _remove_drivers_and_keyframes(id_data: Optional[bpy.types.ID], data_path: Optional[str]) -> None:
    """Remove both drivers and keyframes for a given data path."""
    if not id_data:
        return
    animation_data = getattr(id_data, 'animation_data', None)
    if not animation_data:
        return

    # Remove drivers
    if data_path:
        for fcurve in list(animation_data.drivers):
            if fcurve.data_path == data_path and fcurve.array_index == 0:
                try:
                    animation_data.drivers.remove(fcurve)
                except Exception:
                    pass

        # Remove keyframes
        _remove_existing_keyframes(id_data, data_path)
    else:
        # Remove all drivers and keyframes if no specific path
        while animation_data.drivers:
            try:
                animation_data.drivers.remove(animation_data.drivers[0])
            except Exception:
                pass

        if animation_data.action:
            while animation_data.action.fcurves:
                try:
                    animation_data.action.fcurves.remove(animation_data.action.fcurves[0])
                except Exception:
                    pass


def _assign_scene_driver_var(
    driver: bpy.types.Driver,
    name: str,
    scene: bpy.types.Scene,
    data_path: str,
) -> None:
    var = driver.variables.new()
    var.name = name
    var.type = 'SINGLE_PROP'
    target = var.targets[0]
    target.id_type = 'SCENE'
    target.id = scene
    target.data_path = data_path


def _resolve_route_object(scene: Optional[bpy.types.Scene]) -> Optional[bpy.types.Object]:
    candidates: list[bpy.types.Object] = []
    if scene is not None:
        try:
            candidates.extend(scene.objects)
        except Exception:
            pass
    for obj in bpy.data.objects:
        if obj not in candidates:
            candidates.append(obj)
    for obj in candidates:
        if not obj or getattr(obj, 'type', None) != 'CURVE':
            continue
        modifier = obj.modifiers.get(route_nodes.ROUTE_MODIFIER_NAME)
        if modifier and modifier.type == 'NODES':
            return obj
    return None


def _ensure_route_trace_keyframes(scene: Optional[bpy.types.Scene]) -> bool:
    """Create keyframes for route trace animation using GeoNodes with lead timing."""
    scene = scene or getattr(bpy.context, 'scene', None)
    if scene is None:
        return False

    route_obj = _resolve_route_object(scene)
    if route_obj is None:
        return False

    modifier = route_obj.modifiers.get(route_nodes.ROUTE_MODIFIER_NAME)
    if modifier is None or modifier.type != 'NODES':
        return False

    node_group = getattr(modifier, 'node_group', None)
    if node_group is None:
        return False

    # Get animation parameters from scene properties
    # Use route-specific timing if available, otherwise use car timing
    route_start_frame = getattr(scene, 'blosm_route_start', 1)
    route_end_frame = getattr(scene, 'blosm_route_end', 250)
    lead_frames = getattr(scene, 'blosm_lead_frames', 30)

    # Route trace leads the car by 2x lead frames (similar to OCT28 version)
    # This creates a "draw-ahead" effect where the route appears before the car
    # If route-specific timing is not set, use car timing with lead adjustment
    if route_start_frame == 1 and route_end_frame == 250:  # Default values suggest route props not set
        anim_start_frame = getattr(scene, 'blosm_anim_start', 15)
        anim_end_frame = getattr(scene, 'blosm_anim_end', 150)
        route_start_frame = anim_start_frame - (lead_frames * 2)
        route_end_frame = anim_end_frame - (lead_frames * 2)
    else:
        # Route-specific timing is already set, use as-is
        pass

    # Ensure route starts at least at frame 1
    if route_start_frame < 1:
        route_start_frame = 1
        route_end_frame = anim_end_frame - anim_start_frame + 1

    # Try to find the GeoNodes socket property
    success = False
    prop_name = None

    # Method 1: Try the existing resolution function
    index = _find_gn_input_index(node_group, 'FLOAT', _DEFAULT_FLOAT_NAME)
    if index is not None:
        prop_name = _resolve_gn_input_property(modifier, index)

    # Method 2: If not found, try Socket_10 directly (common fallback)
    if not prop_name and 'Socket_10' in modifier.keys():
        prop_name = 'Socket_10'

    # Set the modifier property to the final value without animation
    if prop_name:
        try:
            modifier[prop_name] = 1.0
            print("[BLOSM] Route trace modifier set to final value (no animation)")
            return True
        except Exception as e:
            print(f"[BLOSM] Error setting GeoNodes property: {e}")

    print(f"[BLOSM] Warning: Could not set route trace property")
    return False



def _ensure_follow_keyframes(
    constraint: Optional[bpy.types.Constraint],
    scene: Optional[bpy.types.Scene],
    *,
    use_lead: bool = False,
) -> bool:
    """Create keyframes for Follow Path constraint animation."""
    if constraint is None or scene is None:
        return False
    id_data = constraint.id_data
    if id_data is None:
        return False

    # Check if this constraint type supports offset_factor
    if not hasattr(constraint, 'offset_factor'):
        print(f"[BLOSM] Constraint {constraint.name} of type {constraint.type} doesn't support offset_factor, skipping keyframes")
        return False

    data_path = f'constraints["{constraint.name}"].offset_factor'

    # Get animation parameters from scene properties
    start_frame = getattr(scene, 'blosm_anim_start', 15)
    end_frame = getattr(scene, 'blosm_anim_end', 150)
    # Interpret blosm_lead_frames as a scalar multiplier for the lead distance
    # along the path (0 disables the offset, 1 = base offset).
    lead_factor = float(getattr(scene, 'blosm_lead_frames', 1))
    if lead_factor < 0.0:
        lead_factor = 0.0

    # Remove existing drivers and keyframes
    _remove_drivers_and_keyframes(id_data, data_path)

    # Create keyframes:
    # - Car constraint animates from 0.0 -> 1.0
    # - Lead constraint uses a small offset delta so it sits slightly ahead
    #   along the path: 0.005 / 1.005 at lead_factor=1, scaled by lead_factor.
    if use_lead and lead_factor > 0.0:
        base_delta = 0.005
        delta = base_delta * lead_factor
        start_value = 0.0 + delta
        end_value = 1.0 + delta
    else:
        start_value = 0.0
        end_value = 1.0

    return _create_animation_keyframes(
        id_data, data_path,
        start_frame=start_frame,
        end_frame=end_frame,
        lead_frames=0,
        start_value=start_value,
        end_value=end_value,
        use_lead=False,
    )




def ensure_follow_keyframes(
    scene: Optional[bpy.types.Scene] = None,
    *,
    car_constraint: Optional[bpy.types.Constraint] = None,
    lead_constraint: Optional[bpy.types.Constraint] = None,
) -> dict[str, bool]:
    """Create keyframes for Follow Path constraints."""
    scene = scene or getattr(bpy.context, "scene", None)
    results = {"car": False, "lead": False}
    if scene is None:
        return results
    if lead_constraint is None:
        # Check for both RouteLead (creation name) and CAR_LEAD (final name)
        lead_obj = bpy.data.objects.get(LEAD_OBJECT_NAME) or bpy.data.objects.get('CAR_LEAD')
        if lead_obj:
            for constraint in lead_obj.constraints:
                if constraint.type == 'FOLLOW_PATH' and constraint.name == LEAD_CONSTRAINT_NAME:
                    lead_constraint = constraint
                    break
    if car_constraint is None:
        car_obj = _resolve_car_object(context=scene)
        if car_obj:
            for constraint in car_obj.constraints:
                if constraint.type == 'FOLLOW_PATH' and constraint.name == CAR_CONSTRAINT_NAME:
                    car_constraint = constraint
                    break
    results["lead"] = _ensure_follow_keyframes(lead_constraint, scene, use_lead=True)
    results["car"] = _ensure_follow_keyframes(car_constraint, scene, use_lead=False)
    return results



def force_follow_keyframes(
    scene: Optional[bpy.types.Scene] = None,
    *,
    car_constraint: Optional[bpy.types.Constraint] = None,
    lead_constraint: Optional[bpy.types.Constraint] = None,
) -> dict[str, bool]:
    """Force creation of all animation keyframes."""
    scene = scene or getattr(bpy.context, 'scene', None)
    results = {'car': False, 'lead': False, 'route': False}
    if scene is None:
        return results

    if lead_constraint is None:
        # Check for both RouteLead (creation name) and CAR_LEAD (final name)
        lead_obj = bpy.data.objects.get(LEAD_OBJECT_NAME) or bpy.data.objects.get('CAR_LEAD')
        if lead_obj:
            for constraint in lead_obj.constraints:
                if constraint.type == 'FOLLOW_PATH' and constraint.name == LEAD_CONSTRAINT_NAME:
                    lead_constraint = constraint
                    break

    if car_constraint is None:
        car_obj = _resolve_car_object(context=scene)
        if car_obj:
            for constraint in car_obj.constraints:
                if constraint.type == 'FOLLOW_PATH' and constraint.name == CAR_CONSTRAINT_NAME:
                    car_constraint = constraint
                    break

    results['lead'] = _ensure_follow_keyframes(lead_constraint, scene, use_lead=True)
    results['car'] = _ensure_follow_keyframes(car_constraint, scene, use_lead=False)
    results['route'] = _ensure_route_trace_keyframes(scene)

    # Ensure Damped Track constraint exists on ASSET_CAR pointing to CAR_LEAD
    lead_obj = bpy.data.objects.get(LEAD_OBJECT_NAME) or bpy.data.objects.get('CAR_LEAD')
    car_obj = _resolve_car_object(context=scene)
    if lead_obj and car_obj:
        damped_track = _ensure_damped_track(car_obj, lead_obj)
        if damped_track:
            print(f"[BLOSM] Damped Track constraint ensured on ASSET_CAR -> CAR_LEAD")
        else:
            print(f"[BLOSM] WARNING Failed to create Damped Track constraint")

    return results


def debug_print_follow_offset_keyframes(
    scene: Optional[bpy.types.Scene] = None,
) -> None:
    """Debug helper: print offset_factor keyframes for car and lead Follow Path constraints.

    Shows frame/time vs value for:
      - ASSET_CAR's Follow Path (car)
      - CAR_LEAD/RouteLead's Follow Path (lead)
    """
    scene = scene or getattr(bpy.context, "scene", None)
    if scene is None:
        print("[BLOSM][DEBUG] No scene available")
        return

    car_obj = _resolve_car_object(context=scene)
    lead_obj = bpy.data.objects.get(LEAD_OBJECT_NAME) or bpy.data.objects.get("CAR_LEAD")

    def _print_constraint_keys(obj: Optional[bpy.types.Object], constraint_name: str, label: str) -> None:
        if obj is None:
            print(f"[BLOSM][DEBUG] {label}: object not found")
            return
        constraint = None
        for c in obj.constraints:
            if c.type == "FOLLOW_PATH" and c.name == constraint_name:
                constraint = c
                break
        if constraint is None:
            print(f"[BLOSM][DEBUG] {label}: Follow Path '{constraint_name}' not found on {obj.name}")
            return

        data_path = f'constraints["{constraint.name}"].offset_factor'
        anim = getattr(constraint.id_data, "animation_data", None)
        action = getattr(anim, "action", None) if anim else None
        if not action:
            print(f"[BLOSM][DEBUG] {label}: no action/keyframes on {obj.name}")
            return

        fcurve = None
        for fc in action.fcurves:
            if fc.data_path == data_path and fc.array_index == 0:
                fcurve = fc
                break
        if fcurve is None:
            print(f"[BLOSM][DEBUG] {label}: no fcurve on {obj.name} for {data_path}")
            return

        print(f"[BLOSM][DEBUG] {label} ({obj.name}) keys for {data_path}:")
        for kp in fcurve.keyframe_points:
            frame = kp.co[0]
            value = kp.co[1]
            print(f"    frame {int(frame)} -> {value:.6f}")

    _print_constraint_keys(car_obj, CAR_CONSTRAINT_NAME, "CAR")
    _print_constraint_keys(lead_obj, LEAD_CONSTRAINT_NAME, "LEAD")

def _ensure_damped_track(car_obj: Optional[bpy.types.Object], lead_obj: Optional[bpy.types.Object]) -> Optional[bpy.types.Constraint]:
    if car_obj is None or lead_obj is None:
        return None
    for constraint in car_obj.constraints:
        if constraint.type == 'DAMPED_TRACK' and constraint.name == DAMPED_TRACK_NAME:
            damped = constraint
            break
    else:
        try:
            damped = car_obj.constraints.new('DAMPED_TRACK')
        except Exception:
            return None
        damped.name = DAMPED_TRACK_NAME
    damped.target = lead_obj
    try:
        damped.track_axis = 'TRACK_X'
    except Exception:
        pass
    try:
        damped.up_axis = 'UP_Z'
    except Exception:
        pass
    return damped


def _ensure_or_create_lead(
    context: bpy.types.Context,
    start_obj: Optional[bpy.types.Object],
    car_obj: Optional[bpy.types.Object],
) -> Optional[bpy.types.Object]:
    # Check for both RouteLead (creation name) and CAR_LEAD (final name)
    lead = bpy.data.objects.get(LEAD_OBJECT_NAME) or bpy.data.objects.get('CAR_LEAD')
    if lead is None:
        lead = bpy.data.objects.new(LEAD_OBJECT_NAME, None)
        lead.empty_display_type = 'PLAIN_AXES'
        lead.empty_display_size = 2.0
        context.scene.collection.objects.link(lead)
    if start_obj:
        try:
            lead.matrix_world = start_obj.matrix_world.copy()
        except Exception:
            lead.rotation_euler = getattr(start_obj, 'rotation_euler', lead.rotation_euler)
    elif car_obj:
        lead.rotation_euler = getattr(car_obj, 'rotation_euler', lead.rotation_euler)
    # Keep lead at the start position; only enforce rotation mode/selection here.
    lead.rotation_mode = 'XYZ'
    lead.select_set(False)
    return lead


def _resolve_car_object(
    provided: Optional[bpy.types.Object] = None,
    *,
    context: Optional[bpy.types.Context] = None,
) -> Optional[bpy.types.Object]:
    """Resolve the primary car object (ASSET_CAR body), not the collection.

    This mirrors the simpler blosm_clean behavior: we always end up with a single
    object to animate, and its children (taxi sign, etc.) follow via parenting.
    """
    if isinstance(provided, bpy.types.Object):
        return provided
    name_cf_target = "asset_car"

    # 1) Prefer an existing ASSET_CAR object in the current blend file.
    direct = bpy.data.objects.get("ASSET_CAR")
    if isinstance(direct, bpy.types.Object) and getattr(direct, "type", "") == "MESH":
        return direct

    # 2) Prefer the last imported car object from the route assets summary.
    summary = route_assets.get_last_summary()
    preferred = summary.get("car_obj") if summary else None
    obj = route_resolve.resolve_object((preferred,) if preferred else None, context=context)
    if isinstance(obj, bpy.types.Object) and getattr(obj, "type", "") == "MESH":
        return obj

    # 3) Fallback: scan ASSET_CAR collection for a plausible car body mesh,
    #    but avoid picking CAR_TRAIL or other helpers.
    car_collection = bpy.data.collections.get("ASSET_CAR")
    if car_collection:
        mesh_candidates = [
            o
            for o in car_collection.objects
            if getattr(o, "type", "") == "MESH"
        ]
        # Strong preference: exact name ASSET_CAR
        for o in mesh_candidates:
            if (o.name or "") == "ASSET_CAR":
                return o
        # Next: names that clearly look like the car body, not the trail.
        filtered = []
        for o in mesh_candidates:
            name_l = (o.name or "").lower()
            if "trail" in name_l:
                continue
            if any(k in name_l for k in ("asset_car", "car_body", "car")):
                filtered.append(o)
        if filtered:
            return filtered[0]
        if mesh_candidates:
            return mesh_candidates[0]

    return None


def _setup_route_animation_drivers(
    context: bpy.types.Context,
    *,
    route_obj: Optional[bpy.types.Object] = None,
    lead_obj: Optional[bpy.types.Object] = None,
    car_obj: Optional[bpy.types.Object] = None,
) -> DriverSetupResult:
    scene = getattr(context, 'scene', None)
    if not scene:
        return DriverSetupResult(route=None, lead_driver=False, car_driver=False, gn_driver=False, lead_constraint=None, car_constraint=None, gn_socket_name=None, lead_follow_ok=False, car_follow_ok=False, car_damped_ok=False)

    route_obj = route_obj or route_resolve.resolve_route_obj(context)
    if route_obj is None:
        return DriverSetupResult(route=None, lead_driver=False, car_driver=False, gn_driver=False, lead_constraint=None, car_constraint=None, gn_socket_name=None, lead_follow_ok=False, car_follow_ok=False, car_damped_ok=False)
    if hasattr(route_obj.data, 'use_path') and getattr(route_obj.data, 'use_path', True) is not True:
        route_obj.data.use_path = True

    try:
        ensure_summary = route_nodes.ensure_route_nodes(context)
        if isinstance(ensure_summary, dict):
            ensured_route = ensure_summary.get('route_obj')
            if isinstance(ensured_route, bpy.types.Object):
                route_obj = ensured_route
    except Exception as exc:
        print(f"[BLOSM] WARN route_nodes_ensure: {exc}")

    start_obj = bpy.data.objects.get(_START_OBJECT_NAME)
    car_obj = _resolve_car_object(car_obj, context=context)

    # Normalize car + taxi sign hierarchy and place car at the route start.
    if start_obj and car_obj:
        body = car_obj

        # Find taxi/sign meshes associated with the car asset.
        sign_children: list[bpy.types.Object] = []
        car_coll = bpy.data.collections.get("ASSET_CAR")
        for obj in bpy.data.objects:
            if getattr(obj, "type", "") != "MESH":
                continue
            name_l = (obj.name or "").lower()
            if "taxi" not in name_l and "sign" not in name_l:
                continue
            # Prefer signs that live in the ASSET_CAR collection or are parented to the car body.
            in_car_coll = any(
                c is car_coll for c in (getattr(obj, "users_collection", []) or [])
            )
            if obj.parent is body or in_car_coll:
                sign_children.append(obj)

        # Clear any external parent on the car body and reset parent inverse.
        try:
            body.parent = None
            body.matrix_parent_inverse = Matrix.Identity(4)
        except Exception:
            pass

        # For each taxi/sign, force a simple world-space follow of the car using a Copy Location constraint.
        for sign in sign_children:
            try:
                # Clear parenting and reset matrix_parent_inverse so we control world transform explicitly.
                sign.parent = None
                sign.matrix_parent_inverse = Matrix.Identity(4)

                # Remove any existing location drivers or Copy Location constraints we might have added before.
                anim = getattr(sign, "animation_data", None)
                if anim and anim.drivers:
                    for fc in list(anim.drivers):
                        if fc.data_path == "location":
                            try:
                                anim.drivers.remove(fc)
                            except Exception:
                                pass
                for c in list(sign.constraints):
                    if c.type == "COPY_LOCATION" and c.name.startswith("BLOSM_TaxiFollowCar"):
                        try:
                            sign.constraints.remove(c)
                        except Exception:
                            pass

                # Place sign at car position + offset in world space.
                offset = Vector((0.0, 0.0, 1.5))
                sign.matrix_world = body.matrix_world @ Matrix.Translation(offset)

                # Add Copy Location so the sign follows the animated car, preserving the current offset.
                cl = sign.constraints.new("COPY_LOCATION")
                cl.name = "BLOSM_TaxiFollowCar"
                cl.target = body
                cl.use_x = cl.use_y = cl.use_z = True
                cl.use_offset = True
                cl.target_space = "WORLD"
                cl.owner_space = "WORLD"
                print(f"[BLOSM] Copy Location constraint added for taxi sign {sign.name} -> {body.name}")
            except Exception as exc:
                print(f"[BLOSM] Warning while normalizing taxi sign {sign.name}: {exc}")

        # Finally, snap the car body to the Start object (world-space).
        try:
            body.matrix_world = start_obj.matrix_world.copy()
        except Exception:
            body.location = start_obj.location
            try:
                body.rotation_euler = start_obj.rotation_euler
            except Exception:
                pass
    lead_obj = _ensure_or_create_lead(context, start_obj, car_obj if car_obj else None)

    if car_obj:
        car_obj.rotation_mode = 'XYZ'
        car_obj.hide_viewport = False
        car_obj.hide_render = False
        try:
            car_obj.hide_set(False)
        except AttributeError:
            pass
        # Normalize car height in local Z while preserving XY from Start.
        try:
            loc = list(car_obj.location)
            loc[2] = 1.5
            car_obj.location = tuple(loc)
        except Exception:
            pass
        car_obj.select_set(False)

    damped_track = _ensure_damped_track(car_obj, lead_obj)

    lead_constraint = _ensure_follow_constraint(lead_obj, LEAD_CONSTRAINT_NAME)
    car_constraint = _ensure_follow_constraint(car_obj, CAR_CONSTRAINT_NAME)
    _configure_follow_path(lead_constraint, route_obj)
    _configure_follow_path(car_constraint, route_obj)

    lead_driver = _ensure_follow_keyframes(lead_constraint, scene, use_lead=True)
    car_driver = _ensure_follow_keyframes(car_constraint, scene, use_lead=False)


    if lead_constraint:
        lead_constraint.offset_factor = 0.0
    if car_constraint:
        car_constraint.offset_factor = 0.0

    modifier = route_obj.modifiers.get(route_nodes.ROUTE_MODIFIER_NAME) if route_obj else None
    gn_socket_name = None
    if modifier and modifier.type == 'NODES' and modifier.node_group:
        gn_index = _find_gn_input_index(modifier.node_group, 'FLOAT', _DEFAULT_FLOAT_NAME)
        gn_socket_name = _resolve_gn_input_property(modifier, gn_index)
    gn_driver = bool(modifier and modifier.type == 'NODES' and modifier.node_group)

    lead_follow_ok = bool(
        lead_constraint
        and lead_constraint.target is route_obj
        and getattr(lead_constraint, 'use_fixed_position', True)
    )
    car_follow_ok = bool(
        car_constraint
        and car_constraint.target is route_obj
        and getattr(car_constraint, 'use_fixed_position', True)
    )

    # ASSET_CAR should have Damped Track constraint to CAR_LEAD
    track_ok = bool(
        damped_track
        and getattr(damped_track, 'target', None) is lead_obj
        and getattr(damped_track, 'track_axis', 'TRACK_X') == 'TRACK_X'
    )
    up_axis_ok = True
    if damped_track and hasattr(damped_track, 'up_axis'):
        up_axis_ok = getattr(damped_track, 'up_axis', 'UP_Z') == 'UP_Z'
    car_damped_ok = track_ok and up_axis_ok

    lead_target = (0.0, 0.0, 1.5)
    lead_at_target = False
    if lead_obj:
        try:
            lead_at_target = all(abs(float(coord) - target) <= 1e-4 for coord, target in zip(lead_obj.location, lead_target))
        except Exception:
            lead_at_target = False
    if start_obj and lead_obj and not lead_at_target:
        try:
            lead_pos = Vector(lead_obj.matrix_world.translation)
            start_pos = Vector(start_obj.matrix_world.translation)
            if (lead_pos - start_pos).length > 0.05:
                print('[BLOSM] WARN route_lead_start_offset')
        except Exception:
            pass

    print(
        f"[BLOSM] route_anim_setup: lead_fp={lead_follow_ok}, car_fp={car_follow_ok}, car_dt={car_damped_ok}, lead_drv={lead_driver}, car_drv={car_driver}"
    )
    print(f"[BLOSM] route_anim_setup: CAR_LEAD FollowPath={lead_follow_ok}, ASSET_CAR DampedTrack={car_damped_ok}")

    return DriverSetupResult(
        route=route_obj,
        lead_driver=lead_driver,
        car_driver=car_driver,
        gn_driver=gn_driver,
        lead_constraint=lead_constraint,
        car_constraint=car_constraint,
        gn_socket_name=gn_socket_name,
        lead_follow_ok=lead_follow_ok,
        car_follow_ok=car_follow_ok,
        car_damped_ok=car_damped_ok,
    )


__all__ = (
    'DriverSetupResult',
    '_find_gn_input_index',
    '_resolve_gn_input_property',
    '_setup_route_animation_drivers',
    'LEAD_OBJECT_NAME',
    'LEAD_CONSTRAINT_NAME',
    'CAR_CONSTRAINT_NAME',
    'DAMPED_TRACK_NAME',
)
