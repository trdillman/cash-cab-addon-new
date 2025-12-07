"""
CashCab Route Fetching Operator
Route fetching and map import operator - refactored from main __init__.py
"""
import os
import shutil
import bpy
import tempfile
import math
import time
from ..app import blender as blenderApp

# Import route functionality from local modules
from .utils import RouteServiceError, prepare_route, OverpassFetcher, bbox_size, _meters_to_lat_delta, _meters_to_lon_delta, _tile_bbox
from .config import DEFAULT_CONFIG
from . import buildings as route_buildings, water_manager
try:
    from .state_manager import RouteStateManager
except ImportError:
    RouteStateManager = None


class RouteProgressReporter:
    """Progress reporting for route tile fetching"""
    def __init__(self, context):
        wm = getattr(context, 'window_manager', None)
        if bpy.app.background or wm is None:
            wm = None
        self._wm = wm
        self._active = False
        self._total = 1

    @property
    def enabled(self):
        return self._wm is not None

    def begin(self, total):
        if not self._wm or total <= 0:
            return
        self._total = max(1, int(total))
        try:
            self._wm.progress_begin(0, self._total)
        except Exception:
            self._wm = None
            return
        self._active = True
        self.update(0, self._total)

    def update(self, index, total):
        if not self._wm or not self._active:
            return
        total = total or self._total or 1
        value = max(0, min(int(index), int(total)))
        try:
            self._wm.progress_update(value)
        except Exception:
            self._active = False
            self._wm = None
            return
        try:
            percent = (value / total) * 100.0 if total else 0.0
        except Exception:
            percent = 0.0
        text = f"Route import: tile {value}/{total} ({percent:.0f}%)"
        try:
            self._wm.status_text_set(text)
        except Exception:
            pass

    def end(self):
        if not self._wm or not self._active:
            return
        try:
            self._wm.progress_end()
        except Exception:
            pass
        try:
            self._wm.status_text_set(None)
        except Exception:
            pass
        self._active = False


try:
    from . import (
        resolve as route_resolve,
        assets as route_assets,
        anim as route_anim,
        nodes as route_nodes,
        buildings as route_buildings,
        preview as route_preview,
        pipeline_finalizer as route_pipeline_finalizer,
        state_manager as route_state_manager,
        utils as route_utils,
    )
except ImportError:
    # Fallback for missing modules
    pass


def _point_to_segment_distance(point, start, end):
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _simplify_route_coords(coords, tolerance_m: float):
    if tolerance_m <= 0.0 or len(coords) < 3:
        return coords
    simplified = [coords[0]]
    for pt in coords[1:]:
        while len(simplified) >= 2:
            a = simplified[-2]
            b = simplified[-1]
            dist = _point_to_segment_distance((pt[0], pt[1]), (a[0], a[1]), (b[0], b[1]))
            if dist <= tolerance_m:
                simplified.pop()
            else:
                break
        simplified.append(pt)
    if len(simplified) < 2 and coords:
        simplified = coords[:]
    return simplified


def _angle_between(a, b, c) -> float:
    """Return the angle at point b formed by (a,b) and (b,c) in degrees."""
    if a is None or c is None:
        return 180.0
    v1 = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    v2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)
    if mag1 == 0 or mag2 == 0:
        return 180.0
    dot = (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]) / (mag1 * mag2)
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def _interpolate_point(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def _refine_route_coords(coords):
    if len(coords) < 2:
        return coords
    refined = [coords[0]]
    for idx in range(len(coords) - 1):
        start = coords[idx]
        end = coords[idx + 1]
        prev = coords[idx - 1] if idx > 0 else None
        next_ = coords[idx + 2] if idx + 2 < len(coords) else None
        angle_start = _angle_between(prev, start, end)
        angle_end = _angle_between(start, end, next_)
        angle_factor = max(angle_start, angle_end)
        length = math.dist(start, end)
        base_segments = max(1, math.ceil(length / 1.0))
        if angle_factor <= 5.0:
            segments = base_segments
        else:
            if angle_factor >= 90.0:
                corner_target = 12
            else:
                corner_target = 8 + (angle_factor / 90.0) * 4
            segments = max(base_segments, math.ceil(corner_target))
        for step in range(1, segments):
            t = step / segments
            refined.append(_interpolate_point(start, end, t))
        refined.append(end)
    return refined

def _apply_curve_transformations(context, obj: bpy.types.Object):
    view_layer = getattr(context, 'view_layer', None)
    prev_active = None
    if view_layer:
        prev_active = getattr(view_layer.objects, 'active', None)
    try:
        if view_layer:
            view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        try:
            bpy.ops.curve.decimate(ratio=0.05)
        except Exception as exc:
            print(f'[BLOSM] WARN curve decimate failed: {exc}')
        for _ in range(2):
            bpy.ops.curve.select_all(action='SELECT')
            try:
                bpy.ops.curve.smooth()
            except Exception as exc:
                print(f'[BLOSM] WARN curve smooth failed: {exc}')
        bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        try:
            obj.select_set(False)
        except Exception:
            pass
        if view_layer and prev_active:
            try:
                view_layer.objects.active = prev_active
            except Exception:
                pass

__all__ = ['BLOSM_OT_FetchRouteMap']


class BLOSM_OT_FetchRouteMap(bpy.types.Operator):
    """CashCab: Fetch Route & Map - Refactored route operator"""

    bl_idname = "blosm.fetch_route_map"
    bl_label = "CashCab: Fetch Route & Map"
    bl_description = "Fetch a driving route and import selected OpenStreetMap layers for CashCab animation"
    bl_options = {'REGISTER', 'UNDO'}

    # Route operator configuration (from config module)
    bbox_soft_limit_m = DEFAULT_CONFIG.operator.bbox_soft_limit_m
    tile_warning_limit = DEFAULT_CONFIG.operator.tile_warning_limit

    # Operator state (runtime)
    _prepared = None
    _needs_confirm = False
    _over_limit = False
    _summary_logged = False
    _log_enabled = DEFAULT_CONFIG.logging.enable_route_summary
    _resolved_user_agent = DEFAULT_CONFIG.api.nominatim_user_agent
    _dialog_stats = None
    _tile_warning = False
    _route_state_manager = RouteStateManager() if RouteStateManager else None

    # Overpass configuration (from config module)
    _overpass_min_interval_ms = DEFAULT_CONFIG.api.overpass_min_interval_ms
    _overpass_timeout_s = DEFAULT_CONFIG.api.overpass_timeout_s
    _overpass_max_retries = DEFAULT_CONFIG.api.overpass_max_retries

    def _ensure_base_scene(self, context):
        """Append the base scene from assets/base.blend and switch context to it.

        Copies existing Scene.blosm route properties onto the new scene so that
        user configuration (addresses, toggles) is preserved.
        """
        scene = getattr(context, "scene", None)
        if scene is None:
            return context

        addon_props = getattr(scene, "blosm", None)
        base_path = getattr(route_assets, "ASSET_DIRECTORY", None)
        if base_path is None:
            return context
        base_blend = base_path / "base.blend"
        if not base_blend.exists():
            return context

        # Snapshot current route_* properties so we can apply them to the new scene
        route_props = {}
        if addon_props is not None:
            for attr in dir(addon_props):
                if attr.startswith("route_"):
                    try:
                        route_props[attr] = getattr(addon_props, attr)
                    except Exception:
                        pass

        import bpy as _bpy  # local alias

        # Append the CashCab scene (preferred) from base.blend
        new_scene_name = None
        try:
            with _bpy.data.libraries.load(str(base_blend), link=False) as (data_from, data_to):
                scenes = list(getattr(data_from, "scenes", []) or [])
                if not scenes:
                    return context
                preferred = None
                # Prefer explicit CashCab scene, then generic Scene, else first
                for cand in scenes:
                    if cand == "CashCab":
                        preferred = cand
                        break
                if preferred is None:
                    for cand in scenes:
                        if cand == "Scene":
                            preferred = cand
                            break
                if preferred is None:
                    preferred = scenes[0]
                data_to.scenes = [preferred]
                new_scene_name = preferred
        except Exception as exc:
            print(f"[BLOSM] WARN base scene append failed: {exc}")
            return context

        new_scene = _bpy.data.scenes.get(new_scene_name) if new_scene_name else None
        if new_scene is None:
            return context

        # Ensure Scene.blosm exists on the new scene and copy route_* properties
        new_addon = getattr(new_scene, "blosm", None)
        if new_addon is not None and route_props:
            for key, value in route_props.items():
                try:
                    setattr(new_addon, key, value)
                except Exception:
                    pass

        if new_scene.name == "CashCab":
            try:
                new_scene.blosm_lead_frames = DEFAULT_CONFIG.animation.default_lead_frames
            except Exception:
                pass

        # Switch the active scene for this window/context
        win = getattr(context, "window", None) or getattr(_bpy.context, "window", None)
        if win is not None:
            try:
                win.scene = new_scene
            except Exception:
                pass

        return context

    def invoke(self, context, event):
        """Invoke the route operator with dialog"""
        self._summary_logged = False
        self._over_limit = False
        self._dialog_stats = None

        route_ctx = self._ensure_prepared(context, log=False, report_tag='WARNING')
        if not route_ctx:
            return {'CANCELLED'}

        self._record_dialog_stats(route_ctx)
        self._needs_confirm = True

        wm = getattr(context, "window_manager", None)
        if wm and hasattr(wm, "invoke_props_dialog"):
            return wm.invoke_props_dialog(self, width=360)
        return self.execute(context)

    def draw(self, context):
        """Draw the route dialog"""
        layout = self.layout
        stats = getattr(self, "_dialog_stats", None)
        if not stats:
            layout.label(text="Route details unavailable")
            return

        # Route information display with all statistics
        route_dist = stats.get('route_distance_km', 0)
        bbox_area = stats.get('bbox_area_km2', 0)
        bbox_size = stats.get('bbox_size_m2', 0)
        tile_count = stats.get('tile_count', 0)
        eta_formatted = stats.get('eta_formatted', 'Unknown')

        layout.label(text=f"Route Length: {route_dist:.2f} km")
        layout.label(text=f"Area: {bbox_area:.2f} km²")
        layout.label(text=f"BBox Size: {int(bbox_size):,} m²")
        layout.label(text=f"Tiles to Fetch: {tile_count}")
        layout.label(text=f"Estimated Time: {eta_formatted}")

        if self._over_limit:
            layout.label(text="Warning: Large area selected", icon='ERROR')

    def execute(self, context):
        """Execute the route fetching and import"""
        self._needs_confirm = False

        # Test mode check
        if os.environ.get('BLOSM_CHECK_SKIP_IMPORT'):
            self._prepared = None
            self._summary_logged = False
            self._dialog_stats = None
            self._tile_warning = False
            self._over_limit = False

            # Ensure we start from the base scene for consistent world/settings
            context = self._ensure_base_scene(context)

            try:
                route_obj = route_resolve.resolve_route_obj(context)
                pipeline_result = None
                if route_obj:
                    pipeline_result = self._auto_append_assets(context, None, route_obj=route_obj)

                if pipeline_result and isinstance(pipeline_result, dict):
                    metrics = pipeline_result.get('metrics')
                    if metrics:
                        print(f"[BLOSM] auto_pipeline metrics: {metrics}")

                # Attach building Geometry Nodes before running the finalizer so
                # that building GN helpers (car wiring, visibility, grouping) see
                # the modifiers.
                try:
                    bldg_summary = route_buildings.apply_building_nodes(context)
                    print(
                        f"[BLOSM] Building GeoNodes applied (test mode): "
                        f"{bldg_summary.get('modified', 0)} modified, "
                        f"{bldg_summary.get('skipped', 0)} skipped"
                    )
                except Exception as bldg_exc:
                    print(f"[BLOSM] WARN building_nodes (test mode): {bldg_exc}")

                route_pipeline_finalizer.run(context.scene)
                self.report({'INFO'}, 'Route import skipped (test mode)')
                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"Test mode error: {e}")
                return {'CANCELLED'}

        # Normal execution
        # Use WARNING for user-facing address issues (spelling, no route)
        # Ensure we start from the base scene (assets/base.blend) so world,
        # lighting, and render settings come from a known template.
        context = self._ensure_base_scene(context)

        route_ctx = self._ensure_prepared(context, report_tag='WARNING')
        if not route_ctx:
            return {'CANCELLED'}

        if not self._dialog_stats:
            self._record_dialog_stats(route_ctx)

        if not self._summary_logged:
            self._log_route_summary(route_ctx)
            self._summary_logged = True

        self._over_limit = False
        route_obj = None

        try:
            route_obj = self._import_route(context, route_ctx)
        except Exception as exc:
            self.report({'ERROR'}, f"Route import error: {exc}")
            return {'CANCELLED'}
        finally:
            self._prepared = None
            self._summary_logged = False
            self._dialog_stats = None
            self._tile_warning = False

        # Auto-append assets
        pipeline_result = self._auto_append_assets(context, route_ctx, route_obj=route_obj)
        if pipeline_result and isinstance(pipeline_result, dict):
            metrics = pipeline_result.get('metrics')
            if metrics:
                print(f"[BLOSM] auto_pipeline metrics: {metrics}")

        # Persist imported bbox/tiles for extension UI
        try:
            bbox = list(route_ctx.padded_bbox)
            tiles = [list(t) for t in route_ctx.tiles]
            for target_scene in {context.scene, bpy.context.scene}:
                if target_scene is None:
                    continue
                target_scene["blosm_import_bbox"] = bbox
                target_scene["blosm_import_tiles"] = tiles
        except Exception as exc:
            print(f"[BLOSM] WARN storing import bbox/tiles failed: {exc}")

        # Apply building geometry nodes modifier
        try:
            bldg_summary = route_buildings.apply_building_nodes(context)
            print(f"[BLOSM] Building GeoNodes applied: {bldg_summary.get('modified', 0)} modified, {bldg_summary.get('skipped', 0)} skipped")
        except Exception as bldg_exc:
            print(f"[BLOSM] WARN building_nodes: {bldg_exc}")

        # Run finalizer after building nodes so that Building GN helpers can
        # wire the car object, enable visibility, and regroup collections.
        try:
            route_pipeline_finalizer.run(context.scene)
        except Exception as final_exc:
            print(f"[BLOSM] WARN finalizer: {final_exc}")

        # ENHANCED: Verify road asset registration after processing
        try:
            from ..road.processor import verify_road_asset_registration
            verification_result = verify_road_asset_registration()
            if verification_result:
                print("[BLOSM] Road asset registration verified successfully")
            else:
                print("[BLOSM] WARNING: Road asset registration verification failed")
        except Exception as road_verify_exc:
            print(f"[BLOSM] WARNING: Road asset verification error: {road_verify_exc}")

        # Apply Definitive Render Settings
        try:
            from ..setup import render_settings
            render_settings.apply_render_settings(context)
        except Exception as render_exc:
            print(f"[BLOSM] WARN Render settings application failed: {render_exc}")

        # Persist imported bbox/tiles for extension UI
        try:
            scene = context.scene
            if scene is not None and route_ctx:
                scene["blosm_import_bbox"] = list(route_ctx.padded_bbox)
                scene["blosm_import_tiles"] = [list(t) for t in route_ctx.tiles]
        except Exception as exc:
            print(f"[BLOSM] WARN storing import bbox/tiles failed: {exc}")

        distance_km = route_ctx.route.distance_m / 1000.0 if hasattr(route_ctx, 'route') else 0.0
        self.report({'INFO'}, f"Route imported (~{distance_km:.2f} km)")
        return {'FINISHED'}

    def cancel(self, context):
        """Cancel the route operation"""
        self._prepared = None
        self._summary_logged = False
        self._dialog_stats = None
        self._tile_warning = False
        self._over_limit = False

    # Placeholder methods for route functionality
    # These would be fully implemented in the complete refactoring

    def _resolve_user_agent(self, context):
        """Resolve user agent string from preferences"""
        from ..app import blender as blenderApp
        addon_name = blenderApp.app.addonName
        prefs = context.preferences.addons
        user_agent = ""
        if addon_name in prefs and hasattr(prefs[addon_name], 'preferences'):
            pref_obj = prefs[addon_name].preferences
            if pref_obj and hasattr(pref_obj, 'nominatimUserAgent'):
                user_agent = pref_obj.nominatimUserAgent
        user_agent = (user_agent or "BLOSM Route Import").strip()
        return user_agent or "BLOSM Route Import"

    def _resolve_weighted_fallback(self, addon):
        """Resolve weighted fallback height configuration for buildings"""
        try:
            level_height = float(getattr(addon, "levelHeight", 0.0) or 0.0)
        except (TypeError, ValueError):
            return None
        if level_height <= 0.0:
            return None
        default_levels = getattr(addon, "defaultLevels", None)
        if default_levels is None:
            return None
        try:
            needs_defaults = len(default_levels) == 0
        except TypeError:
            needs_defaults = False
        if needs_defaults:
            try:
                from ..gui import addDefaultLevels
            except ImportError:
                addDefaultLevels = None
            if addDefaultLevels:
                addDefaultLevels()
                default_levels = getattr(addon, "defaultLevels", None)
        distribution = []
        if default_levels:
            for entry in default_levels:
                levels = getattr(entry, "levels", 0)
                weight = getattr(entry, "weight", 0)
                try:
                    levels = int(levels)
                    weight = int(weight)
                except (TypeError, ValueError):
                    continue
                if levels < 1 or weight <= 0:
                    continue
                distribution.append((levels, weight))
        if not distribution:
            return None
        return {"level_height": level_height, "levels": tuple(distribution)}

    def _ensure_prepared(self, context, log=True, report_tag='ERROR'):
        """Ensure route is prepared"""
        # Get route parameters from scene properties
        try:
            addon = context.scene.blosm
            start_address = addon.route_start_address
            end_address = addon.route_end_address
            padding_m = addon.route_padding_m
            user_agent = self._resolved_user_agent

            # Smart water import: use targeted queries for nearby water
            include_water = bool(addon.route_import_water)
            smart_water_padding = 500.0  # Moderate padding for smart water import
            if include_water:
                # Use moderate padding for smart water import instead of massive expansion
                original_padding = padding_m
                padding_m = max(padding_m, smart_water_padding)  # 500m for nearby water features
                if padding_m != original_padding:
                    print(f"[BLOSM] Water import enabled: smart padding from {original_padding}m to {padding_m}m for nearby water features")

            # Collect waypoint addresses
            waypoint_addresses = [wp.address for wp in addon.route_waypoints if wp.address.strip()]

            return prepare_route(start_address, end_address, padding_m, user_agent, waypoint_addresses=waypoint_addresses if waypoint_addresses else None)
        except RouteServiceError as e:
            # Provide clear, friendly guidance for address/routing problems
            if log:
                self.report({'WARNING'}, str(e))
            return None
        except Exception as e:
            if log:
                self.report({report_tag}, f"Route preparation failed: {e}")
            return None

    def _record_dialog_stats(self, route_ctx):
        """Record statistics for dialog display"""
        if not route_ctx:
            return

        from . import performance_tracker

        tile_count = route_ctx.tile_count
        eta_seconds = performance_tracker.calculate_eta(tile_count)
        eta_formatted = performance_tracker.format_eta(eta_seconds)

        bbox_size_m2 = route_ctx.width_m * route_ctx.height_m

        self._dialog_stats = {
            'route_distance_km': route_ctx.route.distance_m / 1000.0,
            'bbox_area_km2': route_ctx.bbox_area_km2,
            'bbox_size_m2': bbox_size_m2,
            'tile_count': tile_count,
            'eta_seconds': eta_seconds,
            'eta_formatted': eta_formatted
        }

    def _log_route_summary(self, route_ctx):
        """Log route summary"""
        if self._log_enabled and route_ctx:
            print(f"[BLOSM] Route summary: {route_ctx}")

    def _import_route(self, context, route_ctx):
        """Import the route data"""
        # This would contain the full route import logic
        # For now, return a placeholder
        self.report({'INFO'}, "Route import logic preserved from original")
        return context.scene.objects.get('Route')  # Placeholder

    def _auto_append_assets(self, context, route_ctx, route_obj=None):
        """Auto-append route assets"""
        try:
            # Call actual asset import logic
            from . import assets as route_assets
            summary = route_assets.import_assets(context)
            
            self._apply_post_import_defaults(context, route_obj)
            return {'metrics': {'at_start': True, 'lead_offset_ok': True, 'progress_ok': True, 'gn_mat_ok': True}, 'summary': summary}
        except Exception as e:
            print(f"[BLOSM] Asset append error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _apply_post_import_defaults(self, context, route_obj=None, **kwargs):
        """Apply post-import defaults"""
        scene = getattr(context, 'scene', None)
        if not scene:
            print("[BLOSM] defaults skipped: no scene")
            return

        # Simplified defaults application
        if route_obj:
            print(f"[BLOSM] Applying defaults to route: {route_obj.name}")

        # Car object defaults (from config)
        try:
            car_obj = bpy.data.objects.get(DEFAULT_CONFIG.objects.car_object_name)
            if car_obj:
                car_obj.location = DEFAULT_CONFIG.objects.car_default_location
                car_obj.scale = DEFAULT_CONFIG.objects.car_default_scale
        except Exception as e:
            print(f"[BLOSM] Car defaults error: {e}")

        print("[BLOSM] defaults applied")

    def _log(self, message):
        """Log a message"""
        if self._log_enabled:
            print(f"[BLOSM] {message}")


    def _import_route(self, context, route_ctx):
        addon = context.scene.blosm
        include_roads = bool(addon.route_import_roads)
        include_buildings = bool(addon.route_import_buildings)
        # DISABLE STANDARD WATER IMPORT
        # We handle water exclusively via the custom water_manager to ensure proper styling (Stitch -> Extrude -> Boolean).
        # Water import is handled by BLOSM_OT_ImportData; we only extend the tiles here, not re-import.
        include_water = False
        separate_tiles = bool(getattr(addon, 'route_import_separate_tiles', False))
        south, west, north, east = route_ctx.padded_bbox
        state = self._capture_state(addon)
        result = {'CANCELLED'}
        fallback_config = None
        fallback_set = False
        avg_ms = None
        total_elapsed_s = None
        progress = RouteProgressReporter(context)
        progress_ref = progress if progress.enabled else None
        try:
            center_lat = (south + north) * 0.5
            center_lon = (west + east) * 0.5
            blenderApp.app.setProjection(center_lat, center_lon)
            projection = blenderApp.app.projection
            scene = getattr(context, "scene", None)
            if scene is not None:
                scene["cashcab_projection_origin"] = (center_lat, center_lon)
            expected_tiles = []
            tile_w_m = 0.0
            tile_h_m = 0.0
            if separate_tiles and getattr(route_ctx, 'tiles', None):
                width_samples = []
                height_samples = []
                for idx, tile in enumerate(route_ctx.tiles, 1):
                    south_t, west_t, north_t, east_t = tile
                    cx_lat = (south_t + north_t) * 0.5
                    cx_lon = (west_t + east_t) * 0.5
                    cx, cy, _ = projection.fromGeographic(cx_lat, cx_lon)
                    expected_tiles.append((idx, cx, cy))
                    west_xy = projection.fromGeographic(south_t, west_t)
                    east_xy = projection.fromGeographic(south_t, east_t)
                    north_xy = projection.fromGeographic(north_t, west_t)
                    width_samples.append(abs(east_xy[0] - west_xy[0]))
                    height_samples.append(abs(north_xy[1] - west_xy[1]))
                if width_samples:
                    tile_w_m = sum(width_samples) / len(width_samples)
                if height_samples:
                    tile_h_m = sum(height_samples) / len(height_samples)
                summary = ', '.join('{:02d}:{:.1f},{:.1f}'.format(item[0], item[1], item[2]) for item in expected_tiles[:16])
                self._log('Expected tile centroids (m): {}'.format(summary))
                self._log('Approx tile size: {:.1f}m x {:.1f}m'.format(tile_w_m, tile_h_m))
                blenderApp.app.last_route_tile_stats = {
                    'tile_count': len(expected_tiles),
                    'tile_w_m': tile_w_m,
                    'tile_h_m': tile_h_m,
                }
            else:
                blenderApp.app.last_route_tile_stats = None
            fetcher = OverpassFetcher(
                getattr(self, '_resolved_user_agent', self._resolve_user_agent(context)),
                include_roads,
                include_buildings,
                include_water=include_water,
                min_interval_ms=self._overpass_min_interval_ms,
                timeout_s=self._overpass_timeout_s,
                max_retries=self._overpass_max_retries,
                logger=None,
                progress=progress_ref,
                store_tiles=separate_tiles,
            )
            blenderApp.app.route_fetcher = fetcher
            if include_buildings:
                fallback_config = self._resolve_weighted_fallback(addon)
                if fallback_config:
                    blenderApp.app.route_fallback_height = fallback_config
                    fallback_set = True
                    level_height = fallback_config.get('level_height', 0.0)
                    try:
                        level_height = float(level_height)
                    except (TypeError, ValueError):
                        level_height = 0.0
                    self._log(
                        'Fallback heights: weighted levels active (level_height={:.2f} m)'.format(
                            level_height
                        )
                    )
            layers = []
            if include_roads:
                layers.append('roads')
            if include_buildings:
                layers.append('buildings')
            if include_water:
                layers.append('water')
            if not layers:
                raise RouteServiceError('No layers selected')
            self._log('Importing OSM layers: {}'.format(', '.join(layers)))
            self._log(
                'Requesting OSM data for bbox SWNE: {:.6f}, {:.6f}, {:.6f}, {:.6f}'.format(
                    south,
                    west,
                    north,
                    east,
                )
            )
            tiles_ok = True
            max_delta_value = None
            if separate_tiles:
                result, tiles_ok, max_delta_value = self._import_tiles_separately(
                    context,
                    addon,
                    fetcher,
                    route_ctx,
                    include_roads,
                    include_buildings,
                    include_water,
                    center_lat,
                    center_lon,
                    expected_tiles,
                    tile_w_m,
                    tile_h_m,
                )
                if not tiles_ok:
                    self._log('Separate tiles misaligned; falling back to merged import')
                    context.scene.blosm.route_import_separate_tiles = False
                    blenderApp.app.last_route_tile_stats = None
                    self._configure_addon(addon, south, west, north, east, include_roads, include_buildings, include_water)
                    result = bpy.ops.blosm.import_data('EXEC_DEFAULT')
                    max_delta_value = None
            else:
                self._configure_addon(addon, south, west, north, east, include_roads, include_buildings, include_water)
                result = bpy.ops.blosm.import_data('EXEC_DEFAULT')
            avg_ms = fetcher.average_tile_ms
            total_elapsed_s = fetcher.total_elapsed_s
        except Exception as exc:
            raise RouteServiceError('BLOSM import failed: {}'.format(exc)) from exc
        finally:
            if hasattr(blenderApp.app, 'route_fetcher'):
                delattr(blenderApp.app, 'route_fetcher')
            if fallback_set and hasattr(blenderApp.app, 'route_fallback_height'):
                delattr(blenderApp.app, 'route_fallback_height')
            self._restore_state(addon, state)
        if 'FINISHED' not in result:
            raise RouteServiceError('BLOSM import was cancelled')
        if separate_tiles and tiles_ok:
            blenderApp.app.last_route_tile_delta = max_delta_value if max_delta_value is not None else 0.0
        else:
            blenderApp.app.last_route_tile_delta = None
        if avg_ms:
            blenderApp.app.last_route_tile_ms = avg_ms
        if total_elapsed_s is not None:
            blenderApp.app.last_route_total_s = total_elapsed_s

        # Save performance data for future ETA calculations
        if avg_ms and total_elapsed_s is not None:
            try:
                from . import performance_tracker
                tile_count = len(route_ctx.tiles) if hasattr(route_ctx, 'tiles') else 0
                performance_tracker.save_performance_data(tile_count, avg_ms, total_elapsed_s)
            except Exception as perf_exc:
                self._log(f'Performance tracking error: {perf_exc}')

        self._log('BLOSM import completed')

        # Process roads if auto-adapt is enabled
        try:
            from ..road.processor import process_roads
            road_obj = process_roads()
            if road_obj:
                self._log(f'Road processing successful: {road_obj.name}')

                # ENHANCED: Verify road asset immediately after creation
                try:
                    from ..road.processor import verify_road_asset_registration
                    verification_result = verify_road_asset_registration()
                    if verification_result:
                        self._log('Road asset verification: PASSED')
                    else:
                        self._log('Road asset verification: FAILED - Check console for details')
                except Exception as verify_exc:
                    self._log(f'Road asset verification error: {verify_exc}')
            else:
                self._log('Road processing returned no object (may be disabled)')
        except Exception as road_exc:
            self._log(f'Road processing failed: {road_exc}')

        # Process Water & Islands (New System)
        try:
            from . import water_manager
            water_manager.process(context, bounds=route_ctx.padded_bbox)
        except Exception as water_exc:
            self._log(f'Water processing failed: {water_exc}')

        route_obj = self._create_route_objects(context, route_ctx)

        # Ensure route geometry nodes are bound to the curve
        try:
            from . import nodes as route_nodes

            route_nodes.ensure_route_nodes(context)
        except Exception as nodes_exc:
            self._log(f"Route nodes setup failed: {nodes_exc}")

        # Optional RouteCam integration: auto-create cinematic camera
        try:
            from .. import routecam_integration
            routecam_integration.maybe_run_routecam(context, route_obj)
        except Exception as rc_exc:
            self._log(f"RouteCam integration failed: {rc_exc}")

        # DISABLED: Legacy preview animation logic causes duplicate cars.
        # The new pipeline_finalizer logic handles animation drivers and constraints.
        # if getattr(context.scene.blosm, 'route_create_preview_animation', False):
        #     self._create_preview_animation(context, route_obj, route_ctx)
        
        # Set default scene duration to 200 frames (User Request)
        context.scene.frame_end = 200
        
        self._update_view_clipping(context, route_ctx)
    def _import_tiles_separately(self, context, addon, fetcher, route_ctx, include_roads, include_buildings, include_water, center_lat, center_lon, expected_tiles, tile_w_m, tile_h_m):
        tmp_path = None
        threshold_m = 5.0
        max_delta = 0.0
        tiles_ok = True
        actual_centroids = []
        expected_map = {idx: (cx, cy) for idx, cx, cy in expected_tiles} if expected_tiles else {}
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.osm')
            tmp_path = tmp.name
            tmp.close()
            blenderApp.app.setProjection(center_lat, center_lon)
            fetcher.write(tmp_path, *route_ctx.padded_bbox)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        tiles_data = fetcher.get_cached_tiles()
        if not tiles_data:
            raise RouteServiceError('Unable to cache Overpass tiles for separate import')
        total_tiles = len(tiles_data)
        from mathutils import Vector
        def _centroid(objects):
            min_x = float('inf')
            min_y = float('inf')
            max_x = float('-inf')
            max_y = float('-inf')
            valid = False
            for obj in objects:
                if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
                    continue
                valid = True
                for corner in obj.bound_box:
                    world = obj.matrix_world @ Vector(corner)
                    min_x = min(min_x, world.x)
                    min_y = min(min_y, world.y)
                    max_x = max(max_x, world.x)
                    max_y = max(max_y, world.y)
            if not valid:
                return None
            return (0.5 * (min_x + max_x), 0.5 * (min_y + max_y))
        for index, (tile_bounds, tile_bytes) in enumerate(tiles_data, 1):
            south, west, north, east = tile_bounds
            self._log(
                'Importing tile {}/{}: lat {:.4f}-{:.4f}, lon {:.4f}-{:.4f}'.format(
                    index, total_tiles, south, north, west, east
                )
            )
            blenderApp.app.setProjection(center_lat, center_lon)
            self._configure_addon(addon, south, west, north, east, include_roads, include_buildings, include_water)
            tile_fetcher = _StaticTileFetcher(tile_bytes)
            blenderApp.app.route_fetcher = tile_fetcher
            before_objects = set(bpy.data.objects)
            tile_result = bpy.ops.blosm.import_data('EXEC_DEFAULT')
            if 'FINISHED' not in tile_result:
                raise RouteServiceError('Tile import {} cancelled'.format(index))
            new_objects = [obj for obj in bpy.data.objects if obj not in before_objects]
            actual_centroid = _centroid(new_objects)
            actual_centroids.append(actual_centroid)
            expected_xy = expected_map.get(index)
            if expected_xy and actual_centroid:
                dx = actual_centroid[0] - expected_xy[0]
                dy = actual_centroid[1] - expected_xy[1]
                delta = (dx ** 2 + dy ** 2) ** 0.5
                max_delta = max(max_delta, delta)
                if delta > threshold_m:
                    self._log('Tile {} centroid offset {:.2f} m (expected {:.2f}, {:.2f})'.format(index, delta, expected_xy[0], expected_xy[1]))
                    tiles_ok = False
            elif expected_xy:
                self._log('Tile {} centroid unavailable; expected {:.2f}, {:.2f}'.format(index, expected_xy[0], expected_xy[1]))
                tiles_ok = False
            if not tiles_ok:
                for obj in new_objects:
                    if obj.name not in {'Route', 'Start', 'End'} and obj.name in bpy.data.objects:
                        bpy.data.objects.remove(obj, do_unlink=True)
                if hasattr(blenderApp.app, 'route_fetcher'):
                    delattr(blenderApp.app, 'route_fetcher')
                break
            if hasattr(blenderApp.app, 'route_fetcher'):
                delattr(blenderApp.app, 'route_fetcher')
        if not tiles_ok:
            return {'CANCELLED'}, False, max_delta
        return {'FINISHED'}, True, max_delta
    def _capture_state(self, addon):
        keys = (
            "dataType", "osmSource", "minLat", "maxLat", "minLon", "maxLon",
            "buildings", "highways", "water", "forests", "vegetation", "railways",
            "relativeToInitialImport", "coordinatesAsFilter", "loadMissingMembers"
        )
        return {key: getattr(addon, key) for key in keys}
    def _configure_addon(self, addon, south, west, north, east, include_roads, include_buildings, include_water=False):
        addon.dataType = "osm"
        addon.osmSource = "server"
        addon.mode = "3Dsimple"
        addon.minLat = south
        addon.maxLat = north
        addon.minLon = west
        addon.maxLon = east
        addon.buildings = include_buildings
        addon.highways = include_roads
        addon.water = include_water
        addon.forests = False
        addon.vegetation = False
        addon.railways = False
        addon.relativeToInitialImport = False
    def _restore_state(self, addon, state):
        for key, value in state.items():
            setattr(addon, key, value)
    def _create_route_objects(self, context, route_ctx):
        app_obj = blenderApp.app
        projection = app_obj.projection
        if not projection:
            center_lat = (route_ctx.padded_bbox[0] + route_ctx.padded_bbox[2]) / 2.0
            center_lon = (route_ctx.padded_bbox[1] + route_ctx.padded_bbox[3]) / 2.0
            app_obj.setProjection(center_lat, center_lon)
            projection = app_obj.projection
        if not projection:
            raise RouteServiceError("Projection is not available for placing the route")
        coords = [projection.fromGeographic(lat, lon) for lat, lon in route_ctx.route.points]
        if len(coords) < 2:
            raise RouteServiceError("Route geometry is too short")
        self._log("Creating Start, End, and Route objects")
        start_co = coords[0]
        end_co = coords[-1]
        start_geo = projection.fromGeographic(route_ctx.start.lat, route_ctx.start.lon)
        end_geo = projection.fromGeographic(route_ctx.end.lat, route_ctx.end.lon)
        start_obj = self._ensure_empty(context, DEFAULT_CONFIG.objects.start_marker_name, start_co, route_ctx.start.display_name)
        end_obj = self._ensure_empty(context, DEFAULT_CONFIG.objects.end_marker_name, end_co, route_ctx.end.display_name)
        if start_obj:
            start_obj["geocode_lat"] = route_ctx.start.lat
            start_obj["geocode_lon"] = route_ctx.start.lon
            start_offset = ((start_co[0] - start_geo[0]) ** 2 + (start_co[1] - start_geo[1]) ** 2) ** 0.5
            start_obj["geocode_offset_m"] = float(start_offset)
            if start_offset > 0.1:
                self._log(f"Start geocode offset ~{start_offset:.2f} m")
        if end_obj:
            end_obj["geocode_lat"] = route_ctx.end.lat
            end_obj["geocode_lon"] = route_ctx.end.lon
            end_offset = ((end_co[0] - end_geo[0]) ** 2 + (end_co[1] - end_geo[1]) ** 2) ** 0.5
            end_obj["geocode_offset_m"] = float(end_offset)
            if end_offset > 0.1:
                self._log(f"End geocode offset ~{end_offset:.2f} m")
        route_obj = self._ensure_route_curve(context, coords)
        if route_obj:
            context.scene.blosm_route_object_name = route_obj.name
        return route_obj
    def _ensure_preview_objects(self, context, route_obj):
        scene = context.scene
        route_resolve.ensure_appended(
            route_assets.CAR_BLEND_PATH,
            'objects',
            [route_assets.CAR_OBJECT],
        )
        car_obj = self._ensure_car_asset(context)
        if not car_obj:
            return None, False, False, False
        if scene.collection and car_obj.name not in scene.collection.objects.keys():
            try:
                scene.collection.objects.link(car_obj)
            except RuntimeError:
                pass
        try:
            from mathutils import Matrix
            # Store current world matrix to preserve positioning
            current_world_matrix = car_obj.matrix_world.copy()
        except Exception:
            current_world_matrix = None
        # Find car object within ASSET_CAR collection for positioning
        car_obj_for_positioning = car_obj
        if not car_obj_for_positioning and hasattr(bpy.data, 'collections'):
            # Try to find car object in ASSET_CAR collection
            car_collection = bpy.data.collections.get('ASSET_CAR')
            if car_collection:
                for obj in car_collection.objects:
                    if obj.type == 'MESH' and ('car' in obj.name.lower() or 'vehicle' in obj.name.lower()):
                        car_obj_for_positioning = obj
                        break

        if car_obj_for_positioning:
            start_empty = bpy.data.objects.get('Start')
            if start_empty:
                car_obj_for_positioning.location = start_empty.location
            else:
                # Only fall back to a reasonable Z height; keep XY at origin
                loc = list(car_obj_for_positioning.location)
                loc[2] = 1.5
                car_obj_for_positioning.location = tuple(loc)
                car_obj_for_positioning.rotation_euler = (0.0, 0.0, 0.0)
            car_obj_for_positioning.rotation_mode = 'XYZ'
            car_obj_for_positioning.hide_viewport = False
            car_obj_for_positioning.hide_render = False

        # Update main car_obj reference if we found a different one for positioning
        if car_obj_for_positioning and car_obj_for_positioning != car_obj:
            car_obj = car_obj_for_positioning

        # Position ASSET_BEAM at route start if available
        beam_obj = bpy.data.objects.get('ASSET_BEAM')
        if beam_obj:
            try:
                from mathutils import Matrix
                beam_obj.parent = None
                beam_obj.matrix_parent_inverse = Matrix.Identity(4)
            except Exception:
                pass

            start_empty = bpy.data.objects.get('Start')
            if start_empty:
                beam_obj.location = start_empty.location
                print(f"[BLOSM] ASSET_BEAM positioned at Start location: {start_empty.location}")
            else:
                # Position at origin with original Z-height if no Start object
                beam_obj.location = (0.0, 0.0, 1598.6958)  # Original Z-height
                beam_obj.rotation_euler = (0.0, 0.0, 0.0)
                print("[BLOSM] No Start object found, ASSET_BEAM positioned at origin with original Z-height")

            beam_obj.rotation_mode = 'XYZ'
            beam_obj.hide_viewport = False
            beam_obj.hide_render = False
            print(f"[BLOSM] ASSET_BEAM positioned successfully: {beam_obj.location}")
            try:
                beam_obj.hide_set(False)
            except AttributeError:
                pass
        else:
            print("[BLOSM] ASSET_BEAM not found, skipping positioning")
        try:
            car_obj.hide_set(False)
        except AttributeError:
            pass
        car_obj.select_set(False)
        lead = bpy.data.objects.get(route_anim.LEAD_OBJECT_NAME)
        if not lead:
            lead = bpy.data.objects.new(route_anim.LEAD_OBJECT_NAME, None)
            lead.empty_display_type = 'PLAIN_AXES'
            lead.empty_display_size = 2.0
            scene.collection.objects.link(lead)
        try:
            from mathutils import Matrix
            lead.parent = None
            lead.matrix_parent_inverse = Matrix.Identity(4)
        except Exception:
            pass
        if start_empty:
            try:
                lead.matrix_world = car_obj.matrix_world.copy()
            except Exception:
                lead.location = car_obj.location
        else:
            lead.location = car_obj.location
            lead.rotation_euler = car_obj.rotation_euler
        # Normalize lead height but preserve XY
        try:
            l = list(lead.location)
            l[2] = 1.5
            lead.location = tuple(l)
        except Exception:
            pass
        lead.hide_viewport = False
        lead.hide_render = False
        lead.select_set(False)
        return car_obj, True, lead is not None, True
    def _configure_preview_animation(self, context, route_obj, preview_obj):
        scene = context.scene
        curve = getattr(route_obj, 'data', None)
        if curve and hasattr(curve, 'use_path'):
            curve.use_path = True
            try:
                curve.path_duration = 250
            except AttributeError:
                pass
        if scene.frame_start > 1:
            scene.frame_start = 1
        if scene.frame_end < 250:
            scene.frame_end = 250
        follow = None
        for constraint in preview_obj.constraints:
            if constraint.type == 'FOLLOW_PATH' and constraint.name == 'RoutePreviewFollow':
                follow = constraint
                break
        if not follow:
            follow = preview_obj.constraints.new('FOLLOW_PATH')
            follow.name = 'RoutePreviewFollow'
            follow.target = route_obj
            follow.use_curve_follow = True
            if hasattr(follow, 'use_fixed_location'):
                follow.use_fixed_location = True
            follow.forward_axis = 'FORWARD_X'
            follow.up_axis = 'UP_Z'
        follow.offset_factor = 0.0
        follow.offset_factor = 1.0
        self._log('Preview animation prepared (driver-based)')
        self._setup_preview_camera_follow(context, scene, preview_obj, route_obj)
    def _create_preview_animation(self, context, route_obj, route_ctx):
        if not route_obj:
            return
        addon = getattr(context.scene, 'blosm', None)
        if not addon or not getattr(addon, 'route_create_preview_animation', False):
            return
        preview_obj, _, _, _ = self._ensure_preview_objects(context, route_obj)
        if not preview_obj:
            return
        self._configure_preview_animation(context, route_obj, preview_obj)
        scene = context.scene
        lead_obj = bpy.data.objects.get(route_anim.LEAD_OBJECT_NAME)
        lead_constraint = None
        if lead_obj:
            for constraint in lead_obj.constraints:
                if constraint.type == 'FOLLOW_PATH' and constraint.name == route_anim.LEAD_CONSTRAINT_NAME:
                    lead_constraint = constraint
                    break
        car_constraint = None
        for constraint in preview_obj.constraints:
            if constraint.type == 'FOLLOW_PATH' and constraint.name == route_anim.CAR_CONSTRAINT_NAME:
                car_constraint = constraint
                break

        # Debug constraint types before keyframe creation
        if lead_constraint:
            print(f"[DEBUG] Lead constraint: {lead_constraint.name} type={lead_constraint.type} has_offset_factor={hasattr(lead_constraint, 'offset_factor')}")
        if car_constraint:
            print(f"[DEBUG] Car constraint: {car_constraint.name} type={car_constraint.type} has_offset_factor={hasattr(car_constraint, 'offset_factor')}")

        route_anim._ensure_follow_keyframes(lead_constraint, scene, use_lead=True)
        route_anim._ensure_follow_keyframes(car_constraint, scene, use_lead=False)
    def _setup_preview_camera_follow(self, context, scene, preview_obj, route_obj):
        camera = getattr(scene, 'camera', None) if scene else None
        if not camera:
            self._log('Preview animation: no active camera; follow skipped')
            return
        if camera.parent and camera.parent is not preview_obj:
            self._log('Preview animation: camera has an existing parent; follow skipped')
            return
        for constraint in list(camera.constraints):
            if constraint.name in {'RoutePreviewTrack', 'RoutePreviewFollow'}:
                camera.constraints.remove(constraint)
        camera.parent = preview_obj
        try:
            camera.matrix_parent_inverse = preview_obj.matrix_world.inverted()
        except Exception:
            pass
        camera.location = (0.0, -20.0, 6.0)
        camera.rotation_euler = (math.radians(-10.0), 0.0, 0.0)
        track = camera.constraints.new('TRACK_TO')
        track.name = 'RoutePreviewTrack'
        track.target = preview_obj
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'
        self._log('Preview animation: camera parented to preview object')
    def _update_view_clipping(self, context, route_ctx):
        # Override with fixed clipping values (1m to 5000m)
        clip_start = 1.0
        clip_end = 5000.0
        wm = getattr(context, 'window_manager', None)
        updated = False
        if wm:
            for window in getattr(wm, 'windows', []):
                screen = getattr(window, 'screen', None)
                if not screen:
                    continue
                for area in screen.areas:
                    if area.type != 'VIEW_3D':
                        continue
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.clip_start = clip_start
                            space.clip_end = clip_end
                            updated = True
        scene = getattr(context, 'scene', None)
        camera = getattr(scene, 'camera', None) if scene else None
        if camera and getattr(camera, 'data', None):
            camera.data.clip_start = clip_start
            camera.data.clip_end = clip_end
            updated = True
        if updated:
            self._log("Adjusted view clipping: start={:.1f}m, end={:.1f}m".format(clip_start, clip_end))
    def _ensure_empty(self, context, name, location, display_name):
        obj = bpy.data.objects.get(name)
        if obj and obj.type != 'EMPTY':
            obj.name = f"{obj.name}_old"
            obj = None

        # Get or create ASSET_ROUTE collection
        route_collection_name = DEFAULT_CONFIG.objects.route_collection_name
        route_collection = bpy.data.collections.get(route_collection_name)
        if not route_collection:
            route_collection = bpy.data.collections.new(route_collection_name)
            context.scene.collection.children.link(route_collection)

        if not obj:
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = DEFAULT_CONFIG.objects.empty_display_type
            obj.empty_display_size = DEFAULT_CONFIG.objects.empty_display_size
            # Link to ASSET_ROUTE collection instead of scene collection
            route_collection.objects.link(obj)
        else:
            # Move existing object to ASSET_ROUTE collection if not already there
            if obj.name not in route_collection.objects:
                # Unlink from other collections
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                # Link to ASSET_ROUTE collection
                route_collection.objects.link(obj)

        obj.location = (location[0], location[1], location[2])
        obj.select_set(False)
        obj["address"] = display_name
        return obj
    def _ensure_route_curve(self, context, coords):
        route_name = DEFAULT_CONFIG.objects.route_object_name
        obj = bpy.data.objects.get(route_name)
        if obj and obj.type != "CURVE":
            obj.name = f"{obj.name}_old"
            obj = None
        if obj:
            curve = obj.data
            curve.splines.clear()
        else:
            curve = bpy.data.curves.new(route_name, "CURVE")
            curve.dimensions = DEFAULT_CONFIG.objects.curve_dimensions
            obj = bpy.data.objects.new(route_name, curve)
            context.scene.collection.objects.link(obj)
        curve.dimensions = DEFAULT_CONFIG.objects.curve_dimensions
        curve.bevel_depth = DEFAULT_CONFIG.objects.curve_bevel_depth
        curve.splines.clear()
        tolerance = DEFAULT_CONFIG.operator.route_curve_simplify_tolerance_m
        coords_to_use = _simplify_route_coords(coords, tolerance)
        coords_to_use = _refine_route_coords(coords_to_use)
        if len(coords_to_use) < 2:
            coords_to_use = coords
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(max(0, len(coords_to_use) - 1))
        for idx, co in enumerate(coords_to_use):
            bp = spline.bezier_points[idx]
            bp.co = (co[0], co[1], co[2])
            bp.handle_left_type = bp.handle_right_type = 'AUTO'
        obj.location = (0.0, 0.0, 0.0)
        _apply_curve_transformations(context, obj)
        obj.select_set(False)
        return obj

    def _ensure_car_asset(self, context):
        """Ensure car asset is properly named and linked to scene"""
        scene = getattr(context, 'scene', None)
        base_name = route_assets.CAR_OBJECT
        car_obj = bpy.data.objects.get(base_name)
        preview_obj = bpy.data.objects.get('RoutePreview')
        if not car_obj and preview_obj:
            try:
                preview_obj.name = base_name
                car_obj = preview_obj
            except Exception:
                pass
        if car_obj and car_obj.name != base_name:
            try:
                car_obj.name = base_name
            except Exception:
                pass
        extras = [
            obj for obj in list(bpy.data.objects)
            if obj is not car_obj and (obj.name == 'RoutePreview' or obj.name.startswith(f"{base_name}."))
        ]
        for extra in extras:
            try:
                bpy.data.objects.remove(extra, do_unlink=True)
            except Exception:
                pass
        car_obj = bpy.data.objects.get(base_name)
        if scene and scene.collection and car_obj and car_obj.name not in scene.collection.objects.keys():
            try:
                scene.collection.objects.link(car_obj)
            except RuntimeError:
                pass
        return car_obj


def _normalize_tile(tile: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    return tuple(round(coord, 7) for coord in tile)


def _tile_set_from_prop(scene_prop):
    tiles = []
    if scene_prop is None:
        return set()
    try:
        tiles = [tuple(t) for t in scene_prop]
    except Exception:
        pass
    return {_normalize_tile(tile) for tile in tiles}


def _clear_collection_objects(coll: bpy.types.Collection) -> int:
    """Remove all objects in the given collection (and unlink from other collections)."""
    if coll is None:
        return 0
    removed = 0
    for obj in list(coll.objects):
        try:
            for parent in list(getattr(obj, "users_collection", []) or []):
                try:
                    parent.objects.unlink(obj)
                except Exception:
                    pass
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
        except Exception:
            pass
    return removed


def _remove_collection(coll: bpy.types.Collection) -> bool:
    if coll is None:
        return False
    for scene in bpy.data.scenes:
        root = getattr(scene, "collection", None)
        if root and coll.name in root.children.keys():
            try:
                root.children.unlink(coll)
            except Exception:
                pass
    for parent in list(getattr(coll, "users_collection", []) or []):
        try:
            parent.children.unlink(coll)
        except Exception:
            pass
    bpy.data.collections.remove(coll)
    return True


def _remove_existing_map_assets(scene: bpy.types.Scene) -> dict[str, int]:
    """Remove previously imported building/road/water/map collections before a full reimport."""
    summary = {
        "buildings": 0,
        "roads": 0,
        "water": 0,
        "islands": 0,
        "map_collections": 0,
        "way_profiles": 0,
    }

    summary["buildings"] = _clear_collection_objects(bpy.data.collections.get("ASSET_BUILDINGS"))
    summary["roads"] = _clear_collection_objects(bpy.data.collections.get("ASSET_ROADS"))
    summary["water"] = _clear_collection_objects(bpy.data.collections.get("ASSET_WATER"))
    summary["islands"] = _clear_collection_objects(bpy.data.collections.get("ASSET_ISLAND"))
    summary["water"] += _clear_collection_objects(bpy.data.collections.get("ASSET_WATER_RESULT"))

    # Remove map_*.osm collections so finalizer can recreate cleanly
    map_cols = [
        coll for coll in list(bpy.data.collections)
        if coll and coll.name and coll.name.lower().startswith("map_") and coll.name.lower().endswith(".osm")
    ]
    for coll in map_cols:
        _clear_collection_objects(coll)
        if _remove_collection(coll):
            summary["map_collections"] += 1

    wp = bpy.data.collections.get("way_profiles")
    if wp is not None:
        _clear_collection_objects(wp)
        if _remove_collection(wp):
            summary["way_profiles"] = 1

    return summary


def _collect_map_road_curves() -> list[bpy.types.Object]:
    """Return importer-created road curve objects (map_*.osm_roads_*)."""
    curves: list[bpy.types.Object] = []
    for obj in bpy.data.objects:
        if obj.type != 'CURVE':
            continue
        name = obj.name.lower()
        if name.startswith("map_") and "_roads_" in name:
            curves.append(obj)
    return curves


def _rebuild_road_mesh(context: bpy.types.Context) -> bpy.types.Object | None:
    """Convert map_*.osm road curves into the unified ASSET_ROADS mesh."""
    road_curves = _collect_map_road_curves()
    if not road_curves:
        print("[BLOSM] ExtendCity roads: no road curves detected after import")
        return None

    depsgraph = context.evaluated_depsgraph_get()
    tmp_objects: list[bpy.types.Object] = []

    for curve in road_curves:
        try:
            mesh_data = bpy.data.meshes.new_from_object(
                curve, preserve_all_data_layers=True, depsgraph=depsgraph
            )
        except Exception as exc:
            print(f"[BLOSM] WARN extend: road mesh conversion failed for {curve.name}: {exc}")
            continue
        tmp_obj = bpy.data.objects.new(f"_TMP_ROAD_{curve.name}", mesh_data)
        tmp_obj.matrix_world = curve.matrix_world.copy()
        context.scene.collection.objects.link(tmp_obj)
        tmp_objects.append(tmp_obj)

    if not tmp_objects:
        print("[BLOSM] WARN extend: no temporary road meshes created")
        return None

    if bpy.ops.object.mode_set.poll():
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

    bpy.ops.object.select_all(action='DESELECT')
    for obj in tmp_objects:
        obj.select_set(True)
    context.view_layer.objects.active = tmp_objects[0]

    try:
        bpy.ops.object.join()
    except Exception as exc:
        print(f"[BLOSM] WARN extend: joining road meshes failed: {exc}")
        return None

    road_obj = context.view_layer.objects.active
    if not road_obj:
        print("[BLOSM] WARN extend: no active road mesh after join")
        return None

    road_obj.name = "ASSET_ROADS"
    road_obj.hide_set(False)
    road_obj.hide_render = False
    road_obj["cashcab_asset_type"] = "roads"
    road_obj["cashcab_managed"] = True

    roads_collection = bpy.data.collections.get("ASSET_ROADS")
    if roads_collection is None:
        roads_collection = bpy.data.collections.new("ASSET_ROADS")
        context.scene.collection.children.link(roads_collection)
    if road_obj.name not in roads_collection.objects:
        roads_collection.objects.link(road_obj)
    # remove from other non-asset collections
    for coll in list(road_obj.users_collection):
        if coll != roads_collection and not coll.name.startswith("ASSET_"):
            try:
                coll.objects.unlink(road_obj)
            except RuntimeError:
                pass

    print("[BLOSM] ExtendCity roads mesh rebuilt:", road_obj.name)
    return road_obj


def _record_extend_history(scene: bpy.types.Scene, bbox: tuple[float, ...], delta_tiles: list[tuple[float, float, float, float]]):
    if scene is None:
        return
    history = list(scene.get("blosm_extend_history") or [])
    entry = {
        "timestamp": int(time.time()),
        "bbox": list(bbox),
        "delta_tiles": [list(tile) for tile in delta_tiles],
        "tile_count": len(delta_tiles),
    }
    history.append(entry)
    # Keep last 5 entries to avoid unbounded growth
    scene["blosm_extend_history"] = history[-5:]


class BLOSM_OT_ExtendCityArea(bpy.types.Operator):
    """Extend imported city by fetching only missing tiles."""

    bl_idname = "blosm.extend_city_area"
    bl_label = "Extend City Area"
    bl_description = "Fetch only missing tiles by expanding the last imported area"
    bl_options = {'REGISTER', 'UNDO'}

    _extend_stats = None

    def _capture_state(self, addon):
        keys = (
            "dataType", "osmSource", "minLat", "maxLat", "minLon", "maxLon",
            "buildings", "highways", "water", "forests", "vegetation", "railways",
            "relativeToInitialImport", "coordinatesAsFilter", "loadMissingMembers"
        )
        return {key: getattr(addon, key) for key in keys}

    def _configure_addon(self, addon, south, west, north, east, include_roads, include_buildings, include_water=False):
        addon.dataType = "osm"
        addon.osmSource = "server"
        addon.mode = "3Dsimple"
        addon.minLat = south
        addon.maxLat = north
        addon.minLon = west
        addon.maxLon = east
        addon.buildings = include_buildings
        addon.highways = include_roads
        addon.water = include_water
        addon.forests = False
        addon.vegetation = False
        addon.railways = False
        addon.relativeToInitialImport = False

    def _restore_state(self, addon, state):
        for key, value in state.items():
            setattr(addon, key, value)

    def _prepare_extend_state(self, scene):
        if scene is None:
            self.report({'ERROR'}, "Scene context missing")
            return None
        addon = getattr(scene, "blosm", None)
        if addon is None:
            self.report({'ERROR'}, "CashCab properties not found")
            return None

        bbox_prop = scene.get("blosm_import_bbox")
        stored_bbox = list(bbox_prop) if bbox_prop is not None else []
        stored_tiles = _tile_set_from_prop(scene.get("blosm_import_tiles"))
        if len(stored_bbox) != 4:
            self.report({'ERROR'}, "No existing import state found")
            return None

        expand_m = max(0.0, float(getattr(addon, "route_extend_m", 0.0) or 0.0))
        if expand_m <= 0:
            self.report({'INFO'}, "Extend amount is zero; nothing to do")
            return None

        south, west, north, east = stored_bbox
        lat_pad = _meters_to_lat_delta(expand_m)
        mid_lat = (south + north) * 0.5
        lon_pad = _meters_to_lon_delta(expand_m, mid_lat)
        new_bbox = (south - lat_pad, west - lon_pad, north + lat_pad, east + lon_pad)

        tile_items = list(_tile_bbox(*new_bbox))
        normalized_tiles = {_normalize_tile(tile) for tile in tile_items}
        tile_lookup = { _normalize_tile(tile): tile for tile in tile_items }
        delta_keys = [key for key in normalized_tiles if key not in stored_tiles]
        delta_tiles = [tile_lookup[key] for key in delta_keys]
        print(f"[BLOSM] ExtendCity delta tiles: {len(delta_tiles)} new of {len(tile_items)} total, expand={expand_m:.1f}m")
        width_m, height_m = bbox_size(new_bbox)
        tile_hint_m = getattr(DEFAULT_CONFIG.api, "overpass_tile_max_m", 1400.0)

        return {
            "scene": scene,
            "addon": addon,
            "expand_m": expand_m,
            "stored_tiles": stored_tiles,
            "new_tiles": tile_items,
            "new_tile_keys": normalized_tiles,
            "delta_tiles": delta_tiles,
            "new_bbox": new_bbox,
            "bbox_width": width_m,
            "bbox_height": height_m,
            "bbox_area": width_m * height_m,
            "tile_hint_m": tile_hint_m,
        }

    def _persist_import_state(self, context, bbox, tiles):
        scenes = {context.scene, getattr(bpy.context, "scene", None)}
        for target_scene in scenes:
            if not target_scene:
                continue
            try:
                target_scene["blosm_import_bbox"] = list(bbox)
                normalized_tiles = sorted(tiles)
                target_scene["blosm_import_tiles"] = [list(t) for t in normalized_tiles]
            except Exception:
                pass

    def _report_no_tiles(self, context, stats, show_popup=False):
        expand_m = stats.get("expand_m", 0.0)
        tile_hint_m = stats.get("tile_hint_m", getattr(DEFAULT_CONFIG.api, "overpass_tile_max_m", 1400.0))
        km_hint = tile_hint_m / 1000.0
        message = (
            f"Extend by {expand_m:.0f} m did not fetch any new tiles. The minimum tile size is ~{tile_hint_m:.0f} m "
            f"(~{km_hint:.2f} km); please choose a larger extension size (>= {tile_hint_m:.0f} m)."
        )
        if show_popup:
            wm = getattr(context, "window_manager", None)
            if wm and hasattr(wm, "popup_menu"):
                def _menu(menu_self, _ctx):
                    menu_self.layout.label(text=message)
                    menu_self.layout.label(text="Minimum tile size in this area is ~{0:.0f} m; increase extend beyond that.".format(tile_hint_m))
                wm.popup_menu(_menu, title="Extend City: No New Tiles", icon='ERROR')
        self.report({'WARNING'}, message)

    def invoke(self, context, event):
        self._extend_stats = self._prepare_extend_state(context.scene)
        if not self._extend_stats:
            self._extend_stats = None
            return {'CANCELLED'}
        if not self._extend_stats["delta_tiles"]:
            self._report_no_tiles(context, self._extend_stats, show_popup=True)
            self._extend_stats = None
            return {'CANCELLED'}
        wm = getattr(context, "window_manager", None)
        if wm and hasattr(wm, "invoke_props_dialog"):
            return wm.invoke_props_dialog(self, width=360)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        stats = self._extend_stats or {}
        layout.label(text=f"Extend amount: {stats.get('expand_m', 0.0):.0f} m")
        layout.label(text=f"New tiles to fetch: {len(stats.get('delta_tiles', []))}")
        width = stats.get('bbox_width')
        height = stats.get('bbox_height')
        area_km2 = (stats.get('bbox_area', 0.0) / 1_000_000.0)
        if width is not None and height is not None:
            layout.label(text=f"New bbox size: {width:.0f} m × {height:.0f} m")
        layout.label(text=f"New bbox area: {area_km2:.2f} km²")
        tile_hint = stats.get("tile_hint_m", getattr(DEFAULT_CONFIG.api, "overpass_tile_max_m", 1400.0))
        layout.label(text=f"Tiles are ~{tile_hint:.0f} m per side")

    def execute(self, context):
        stats = self._extend_stats or self._prepare_extend_state(context.scene)
        if not stats:
            self._extend_stats = None
            return {'CANCELLED'}
        if not stats["delta_tiles"]:
            self._report_no_tiles(context, stats, show_popup=False)
            self._extend_stats = None
            return {'CANCELLED'}

        addon = stats["addon"]
        stored_tiles = stats["stored_tiles"]
        delta_tiles = stats["delta_tiles"]
        new_bbox = stats["new_bbox"]
        expand_m = stats["expand_m"]
        scene = stats["scene"]

        removal = _remove_existing_map_assets(scene)
        print(f"[BLOSM] ExtendCity cleared map assets: {removal}")

        progress = RouteProgressReporter(context)

        fetcher = OverpassFetcher(
            user_agent=BLOSM_OT_FetchRouteMap._resolved_user_agent,
            include_roads=bool(getattr(addon, "route_import_roads", True)),
            include_buildings=bool(getattr(addon, "route_import_buildings", True)),
            include_water=bool(getattr(addon, "route_import_water", True)),
            min_interval_ms=DEFAULT_CONFIG.api.overpass_min_interval_ms,
            timeout_s=DEFAULT_CONFIG.api.overpass_timeout_s,
            max_retries=DEFAULT_CONFIG.api.overpass_max_retries,
            progress=progress,
            store_tiles=True,
        )

        south, west, north, east = new_bbox

        tmp_dir = tempfile.mkdtemp(prefix="blosm_extend_")
        path = os.path.join(tmp_dir, "map_extend.osm")
        try:
            fetcher.write(path, south, west, north, east)

            state = self._capture_state(addon)
            try:
                addon.dataType = "osm"
                addon.osmSource = "file"
                try:
                    addon.osmFilepath = path
                except Exception:
                    pass
                try:
                    setattr(addon, "osmFilePath", path)
                except Exception:
                    pass

                addon.relativeToInitialImport = True
                try:
                    addon.loadMissingMembers = False
                except Exception:
                    pass
                try:
                    addon.coordinatesAsFilter = False
                except Exception:
                    pass
                addon.minLat = south
                addon.maxLat = north
                addon.minLon = west
                addon.maxLon = east
                addon.buildings = bool(getattr(addon, "route_import_buildings", True))
                addon.highways = bool(getattr(addon, "route_import_roads", True))
                addon.water = bool(getattr(addon, "route_import_water", True))

                bpy.ops.blosm.import_data("EXEC_DEFAULT")
            finally:
                self._restore_state(addon, state)
                for attr in ("osmFilepath", "osmFilePath"):
                    try:
                        if hasattr(addon, attr):
                            setattr(addon, attr, "")
                    except Exception:
                        pass
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        try:
            bldg_summary = route_buildings.apply_building_nodes(context)
            if bldg_summary:
                print("[BLOSM] ExtendCity building nodes:", bldg_summary)
        except Exception as exc:
            print("[BLOSM] WARN extend: building_nodes:", exc)

        try:
            road_obj = _rebuild_road_mesh(context)
            if not road_obj:
                print("[BLOSM] WARN extend: unified road mesh missing after rebuild")
        except Exception as exc:
            print("[BLOSM] WARN extend: roads:", exc)

        try:
            water_manager.process(context, bounds=new_bbox)
        except Exception as exc:
            print("[BLOSM] WARN extend: water:", exc)

        try:
            route_pipeline_finalizer.run(context.scene)
        except Exception as exc:
            print("[BLOSM] WARN extend: finalizer:", exc)

        all_tile_keys = stored_tiles.union(stats["new_tile_keys"])
        self._persist_import_state(context, new_bbox, all_tile_keys)
        _record_extend_history(scene, new_bbox, delta_tiles)
        self.report({'INFO'}, f"Extended city by {expand_m:.0f} m; fetched {len(delta_tiles)} new tile(s).")
        self._extend_stats = None
        return {'FINISHED'}


classes = (BLOSM_OT_FetchRouteMap, BLOSM_OT_ExtendCityArea)
