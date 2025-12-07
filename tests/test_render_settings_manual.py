import sys
import types


def setup_fake_bpy():
    """Create a minimal fake bpy + mathutils so render_settings can import."""
    # Fake mathutils module
    mathutils_mod = types.ModuleType("mathutils")

    class Vector:
        def __init__(self, *args, **kwargs):
            self.data = args

    class Color:
        def __init__(self, *args, **kwargs):
            self.data = args

    mathutils_mod.Vector = Vector
    mathutils_mod.Color = Color
    sys.modules["mathutils"] = mathutils_mod

    # Fake bpy module
    bpy_mod = types.ModuleType("bpy")

    class FakeDevice:
        def __init__(self, dev_type: str):
            self.type = dev_type
            self.use = False

    class FakeCyclesPrefs:
        def __init__(self):
            self.compute_device_type = "CUDA"
            self.devices = [FakeDevice("OPTIX"), FakeDevice("CUDA")]

    class FakeAddon:
        def __init__(self, preferences):
            self.preferences = preferences

    class FakePreferences:
        def __init__(self):
            self.addons = {"cycles": FakeAddon(FakeCyclesPrefs())}

    class FakeSceneCycles:
        def __init__(self):
            self.use_denoising = False
            self.denoiser = ""
            self.denoising_input_passes = ""
            self.denoising_prefilter = ""
            self.denoising_radius = 0.0
            self.denoising_strength = 0.0
            self.denoising_store_passes = False
            self.denoising_quality = ""
            self.denoising_use_gpu = False

    class FakeScene:
        def __init__(self):
            self.cycles = FakeSceneCycles()

    class FakeViewLayerCycles:
        def __init__(self):
            self.use_denoising = False
            self.denoising_input_passes = ""

    class FakeViewLayer:
        def __init__(self):
            self.cycles = FakeViewLayerCycles()

    class FakeContext:
        def __init__(self):
            self.preferences = FakePreferences()
            self.scene = FakeScene()
            self.view_layer = FakeViewLayer()

    bpy_mod.context = FakeContext()

    # Minimal bpy.types used only for type hints
    bpy_mod.types = types.SimpleNamespace(Scene=object, ViewLayer=object)

    sys.modules["bpy"] = bpy_mod
    return bpy_mod


def run_tests():
    """Run basic validation of render_settings using the fake bpy context."""
    bpy_mod = setup_fake_bpy()

    # Import after stubbing modules so imports resolve correctly
    from setup import render_settings  # type: ignore

    # --- Test: _enable_optix_compute_device sets OPTIX and toggles devices ---
    prefs = bpy_mod.context.preferences
    cycles_addon = prefs.addons["cycles"]
    cycles_prefs = cycles_addon.preferences

    # Pre-condition sanity
    assert cycles_prefs.compute_device_type == "CUDA"
    assert [d.use for d in cycles_prefs.devices] == [False, False]

    render_settings._enable_optix_compute_device()

    # After call, compute_device_type should be OPTIX
    assert cycles_prefs.compute_device_type == "OPTIX", "compute_device_type was not set to OPTIX"

    # Only OPTIX device should be enabled
    dev_states = [(d.type, d.use) for d in cycles_prefs.devices]
    assert dev_states == [("OPTIX", True), ("CUDA", False)], f"Unexpected device states: {dev_states}"

    # --- Test: _configure_denoising sets expected Cycles denoiser options ---
    scene = bpy_mod.context.scene
    view_layer = bpy_mod.context.view_layer

    render_settings._configure_denoising(scene, view_layer)

    c = scene.cycles
    assert c.denoiser == "OPENIMAGEDENOISE"
    assert c.denoising_input_passes == "RGB_ALBEDO_NORMAL"
    assert c.denoising_prefilter == "ACCURATE"
    assert c.denoising_quality == "HIGH"
    assert c.denoising_use_gpu is True
    assert c.use_denoising is True
    assert c.denoising_store_passes is True

    vl_c = view_layer.cycles
    assert vl_c.use_denoising is True
    assert vl_c.denoising_input_passes == "RGB_ALBEDO_NORMAL"

    # --- Test: apply_render_settings wires helpers correctly ---
    # Patch helpers and loader to observe calls without touching disk/compositor.
    flags = {"enable_called": False, "denoise_called": False}

    def fake_enable():
        flags["enable_called"] = True

    def fake_configure(scene_arg, vl_arg):
        flags["denoise_called"] = (scene_arg is scene and vl_arg is view_layer)

    render_settings._enable_optix_compute_device = fake_enable  # type: ignore
    render_settings._configure_denoising = fake_configure  # type: ignore
    render_settings.load_config = lambda: None  # type: ignore

    render_settings.apply_render_settings(bpy_mod.context)

    assert flags["enable_called"] is True, "apply_render_settings did not call _enable_optix_compute_device"
    assert flags["denoise_called"] is True, "apply_render_settings did not call _configure_denoising with context scene/view_layer"

    print("All render_settings tests passed.")


if __name__ == "__main__":
    run_tests()

