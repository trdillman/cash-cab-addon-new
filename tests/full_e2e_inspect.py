"""
Full E2E inspection for route + car pipeline.

Run against an existing .blend (e.g. test_route_import_real.blend):

  blender -b test_route_import_real.blend -P full_e2e_inspect.py

Checks:
  - ROUTE modifiers and subsurf levels
  - ASSET_CAR + taxi sign Copy Location constraints
  - CAR_LEAD Follow Path to ROUTE
  - CAR_TRAIL constraints, modifiers, drivers, bevel profile
"""

import bpy


def check_route():
    print("\n=== ROUTE CHECK ===")
    route = bpy.data.objects.get("ROUTE") or bpy.data.objects.get("Route")
    if not route:
        print("FAIL: ROUTE object not found")
        return False
    ok = True
    mods = list(route.modifiers)
    for i, m in enumerate(mods):
        print(f"  [{i}] {m.name} ({m.type})")
    if len(mods) >= 3:
        if not (mods[0].name == "RouteTrace" and mods[0].type == "NODES"):
            print("FAIL: RouteTrace not first modifier")
            ok = False
        if not (mods[1].name == "RouteSmooth" and mods[1].type == "SMOOTH"):
            print("FAIL: RouteSmooth not second modifier")
            ok = False
        if not (mods[2].name == "RouteSubsurf" and mods[2].type == "SUBSURF"):
            print("FAIL: RouteSubsurf not third modifier")
            ok = False
    subsurf = route.modifiers.get("RouteSubsurf")
    if not subsurf or subsurf.type != "SUBSURF":
        print("FAIL: RouteSubsurf modifier missing")
        ok = False
    else:
        print(f"  RouteSubsurf levels: viewport={subsurf.levels}, render={subsurf.render_levels}")
        if subsurf.levels != 0 or subsurf.render_levels != 1:
            print("FAIL: RouteSubsurf levels do not match (0 viewport, 1 render)")
            ok = False
    print("ROUTE CHECK:", "PASS" if ok else "FAIL")
    return ok


def find_car_and_signs():
    car = bpy.data.objects.get("ASSET_CAR")
    car_coll = bpy.data.collections.get("ASSET_CAR")
    signs = []
    if car:
        for obj in bpy.data.objects:
            if getattr(obj, "type", "") != "MESH":
                continue
            name_l = (obj.name or "").lower()
            if "taxi" not in name_l and "sign" not in name_l:
                continue
            in_car_coll = car_coll and any(c is car_coll for c in getattr(obj, "users_collection", []) or [])
            if obj.parent is car or in_car_coll:
                signs.append(obj)
    return car, signs


def check_car_and_signs():
    print("\n=== CAR + SIGN CHECK ===")
    car, signs = find_car_and_signs()
    ok = True
    if not car:
        print("FAIL: ASSET_CAR object not found")
        return False
    print(f"ASSET_CAR: {car.name}")
    dt = None
    for c in car.constraints:
        if c.type == "DAMPED_TRACK":
            dt = c
            break
    if not dt or not getattr(dt, "target", None):
        print("FAIL: Damped Track constraint to CAR_LEAD missing on ASSET_CAR")
        ok = False
    else:
        print(f"  DampedTrack: target={dt.target.name}, track_axis={dt.track_axis}")
    print(f"Found {len(signs)} taxi/sign objects")
    if not signs:
        print("WARN: No taxi/sign meshes associated with car found")
    for s in signs:
        cl_ok = False
        for c in s.constraints:
            if c.type == "COPY_LOCATION" and c.name.startswith("BLOSM_TaxiFollowCar") and getattr(c, "target", None) is car:
                cl_ok = True
                break
        if not cl_ok:
            print(f"FAIL: {s.name} missing BLOSM_TaxiFollowCar Copy Location to ASSET_CAR")
            ok = False
        else:
            print(f"  OK: {s.name} has BLOSM_TaxiFollowCar -> {car.name}")
    print("CAR + SIGN CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_car_lead_and_follow():
    print("\n=== CAR_LEAD CHECK ===")
    lead = bpy.data.objects.get("CAR_LEAD") or bpy.data.objects.get("RouteLead")
    route = bpy.data.objects.get("ROUTE") or bpy.data.objects.get("Route")
    ok = True
    if not lead:
        print("FAIL: CAR_LEAD/RouteLead object not found")
        return False
    print(f"CAR_LEAD: {lead.name}")
    fp = None
    for c in lead.constraints:
        if c.type == "FOLLOW_PATH":
            fp = c
            break
    if not fp or getattr(fp, "target", None) is not route:
        print(f"FAIL: Follow Path on {lead.name} missing or not targeting ROUTE")
        ok = False
    else:
        print(f"  FollowPath: name={fp.name}, target={fp.target.name}")
    print("CAR_LEAD CHECK:", "PASS" if ok else "FAIL")
    return ok


def check_car_trail():
    print("\n=== CAR_TRAIL CHECK ===")
    ct = bpy.data.objects.get("CAR_TRAIL")
    ok = True
    if not ct:
        print("FAIL: CAR_TRAIL object not found")
        return False
    print(f"CAR_TRAIL: {ct.name}, type={ct.type}")
    if ct.constraints:
        print(f"FAIL: CAR_TRAIL has {len(ct.constraints)} constraint(s)")
        for c in ct.constraints:
            print(f"  - {c.name} ({c.type})")
        ok = False
    else:
        print("  Constraints: 0 (OK)")
    mods = list(ct.modifiers)
    for i, m in enumerate(mods):
        print(f"  [{i}] {m.name} ({m.type})")
    gn = ct.modifiers.get("CarTrailGeo")
    if not gn or gn.type != "NODES":
        print("FAIL: CarTrailGeo GeoNodes modifier missing on CAR_TRAIL")
        ok = False
    cd = getattr(ct, "data", None)
    if hasattr(cd, "animation_data") and cd.animation_data:
        drivers = cd.animation_data.drivers
        print(f"  Curve data drivers: {len(drivers)}")
        for d in drivers:
            expr = getattr(getattr(d, "driver", None), "expression", "")
            print(f"    - {d.data_path} (expr='{expr}')")
        paths = {d.data_path for d in drivers} if drivers else set()
        if "bevel_factor_end" not in paths or "bevel_factor_start" not in paths:
            print("FAIL: CAR_TRAIL missing bevel_factor drivers")
            ok = False
    else:
        print("FAIL: CAR_TRAIL curve data has no animation drivers")
        ok = False
    profile = bpy.data.objects.get("_profile_curve")
    print("  _profile_curve:", profile)
    if not profile:
        print("FAIL: _profile_curve bevel profile object not found")
        ok = False
    bevel_obj = getattr(cd, "bevel_object", None)
    print("  bevel_object:", bevel_obj)
    if not bevel_obj:
        print("FAIL: CAR_TRAIL bevel_object is not set")
        ok = False
    print("CAR_TRAIL CHECK:", "PASS" if ok else "FAIL")
    return ok


def main():
    route_ok = check_route()
    car_sign_ok = check_car_and_signs()
    lead_ok = check_car_lead_and_follow()
    trail_ok = check_car_trail()

    print("\n=== E2E SUMMARY ===")
    print("ROUTE:", "PASS" if route_ok else "FAIL")
    print("CAR+SIGN:", "PASS" if car_sign_ok else "FAIL")
    print("CAR_LEAD:", "PASS" if lead_ok else "FAIL")
    print("CAR_TRAIL:", "PASS" if trail_ok else "FAIL")


if __name__ == "__main__":
    main()

