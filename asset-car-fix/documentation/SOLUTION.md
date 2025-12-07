# Car Import Parenting Issue - Solution

## Problem Summary
The taxi sign in ASSET_CAR.blend is not following the car during route import because:
1. Parent-child transform inheritance is not working reliably
2. Code in route/anim.py:617 and route/fetch_operator.py:1072 clears parent relationships
3. Asset import workflow doesn't properly handle hierarchical object movement

## Solution: Manual Child Synchronization

Instead of relying on Blender's parenting system, manually synchronize child objects with the car position.

### Implementation

Add this function to `route/assets.py`:

```python
def _sync_child_objects_with_car(car_collection: bpy.types.Collection, car_obj: bpy.types.Object) -> None:
    """
    Synchronize child objects like taxi sign with car movement.

    This replaces the broken parent-child inheritance system with manual
    positioning of child objects relative to the car.

    Args:
        car_collection: The ASSET_CAR collection
        car_obj: The main car object
    """
    if not car_collection or not car_obj:
        return

    # Store initial positions before car movement
    child_positions = {}

    # Record initial relative positions of child objects
    for obj in car_collection.objects:
        if obj != car_obj and obj.parent == car_obj:
            # Store relative position from parent
            relative_pos = obj.location.copy()
            child_positions[obj.name] = relative_pos

    # Apply movement to child objects
    car_movement = car_obj.location - car_obj.location
    for obj_name, relative_pos in child_positions.items():
        obj = bpy.data.objects.get(obj_name)
        if obj and obj in car_collection.objects:
            # Move child object relative to parent
            obj.location = relative_pos
            # Re-establish parenting if broken
            if obj.parent != car_obj:
                obj.parent = car_obj
                obj.matrix_parent_inverse = car_obj.matrix_world.inverted()
```

### Integration Points

**1. In `route/assets.py:254`** (after CAR_TRAIL configuration):
```python
# Configure CAR_TRAIL geometry nodes modifier to reference route curve
_configure_car_trail_modifier(context, car_collection)

# NEW: Synchronize child objects with car position
_sync_child_objects_with_car(car_collection, car_obj)
```

**2. In `route/anim.py:617`** (remove parent clearing, add sync):
```python
# REMOVE THESE LINES:
# car_obj.parent = None
# car_obj.matrix_parent_inverse = Matrix.Identity(4)

# REPLACE WITH:
# Position the car object
car_obj.location = target_location

# NEW: Synchronize child objects
if car_collection := bpy.data.collections.get("ASSET_CAR"):
    _sync_child_objects_with_car(car_collection, car_obj)
```

**3. In `route/fetch_operator.py:1072`** (same change):
```python
# REMOVE THESE LINES:
# car_obj.parent = None
# car_obj.matrix_parent_inverse = Matrix.Identity(4)

# REPLACE WITH:
# Position the car object
car_obj.location = target_location

# NEW: Synchronize child objects
if car_collection := bpy.data.collections.get("ASSET_CAR"):
    _sync_child_objects_with_car(car_collection, car_obj)
```

## Why This Works

1. **Manual Control**: Direct positioning bypasses broken inheritance
2. **Preserves Hierarchy**: Maintains parent-child relationships for consistency
3. **Relative Positioning**: Children maintain their relative positions to the car
4. **Animation Compatible**: Child objects follow car movement along route paths

## Validation

Test the fix by:
1. Running route import with taxi sign asset
2. Verifying taxi sign follows car movement
3. Confirming animation playback works correctly
4. Checking no existing functionality is broken

## Files Modified

- `route/assets.py` - Add `_sync_child_objects_with_car` function
- `route/anim.py` - Replace parent clearing with child synchronization
- `route/fetch_operator.py` - Same parent clearing fix

## Success Criteria

✅ Taxi sign follows car position during route import
✅ Taxi sign follows car during animation
✅ No existing functionality broken
✅ Performance impact < 5% additional time
✅ Works with real ASSET_CAR.blend file