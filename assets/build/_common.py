"""Shared helpers for every asset build script in this project.

Usage inside a build script (run with tools/blender.sh):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import _common as C

    C.reset_scene()
    col = C.collection("XB")
    body = C.rounded_box("XB_Body", (0.32, 0.26, 0.43), (0, 0, 0.335), C.material("MAT_Cream"), col=col)
    C.save("assets/xiaobo.blend")
    # previews are rendered by tools/validate.sh into tasks/reports/validation/<asset>/

Rules this module enforces / assumes (see docs/02_conventions.md):
- Units are meters, Z is up, characters face -Y.
- Colors come only from config/style.json (palette keys or the named materials).
- Everything is deterministic: no unseeded randomness.
Tested on Blender 5.2.2 LTS (macOS, Apple Silicon). Also works on 4.2+.
"""
import bpy
import json
import math
import os
import sys
from pathlib import Path

from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]          # project root (video-model/)
STYLE_PATH = ROOT / "config" / "style.json"
_STYLE = None


# --------------------------------------------------------------------------- config
def style():
    """Return config/style.json as a dict (cached)."""
    global _STYLE
    if _STYLE is None:
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            _STYLE = json.load(f)
    return _STYLE


def argv():
    """Arguments passed after `--` on the Blender command line."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def abspath(rel):
    """Project-relative path -> absolute Path."""
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p


# --------------------------------------------------------------------------- color
def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgba(name_or_hex, alpha=1.0):
    """Palette key (e.g. 'teal') or '#RRGGBB' -> linear RGBA tuple for Blender."""
    h = style()["palette"].get(name_or_hex, name_or_hex)
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), alpha)


def rgb(name_or_hex):
    return rgba(name_or_hex)[:3]


# --------------------------------------------------------------------------- scene / collections
def reset_scene():
    """Start from an empty factory scene (deterministic)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.render.fps = style()["fps"]
    return sc


def collection(name, parent=None):
    """Get or create a collection linked under `parent` (default: scene root)."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    parent_col = parent if parent is not None else bpy.context.scene.collection
    if col.name not in parent_col.children:
        parent_col.children.link(col)
    return col


def move_to(obj, col):
    """Make `col` the only collection that contains `obj`."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def empty(name, location=(0, 0, 0), col=None, display="PLAIN_AXES", size=0.1, parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display
    obj.empty_display_size = size
    obj.location = location
    (col or bpy.context.scene.collection).objects.link(obj)
    bpy.context.view_layer.update()
    if parent is not None:
        set_parent(obj, parent)
    return obj


def set_parent(child, parent, keep_world=True):
    """Parent `child` to `parent` keeping its world transform. Updates the depsgraph first, so
    objects whose location was just set (e.g. made with bpy.data.objects.new) are correct."""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.parent_type = "OBJECT"
    if keep_world:
        child.matrix_world = mw
    bpy.context.view_layer.update()
    return child


def parent_to_bone(child, rig, bone, keep_world=True):
    """Rigid bone parenting (no weights): child follows `rig.pose.bones[bone]`, world transform kept."""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = rig
    child.parent_type = "BONE"
    child.parent_bone = bone
    bpy.context.view_layer.update()
    if keep_world:
        child.matrix_world = mw
    bpy.context.view_layer.update()
    return child


# --------------------------------------------------------------------------- materials
def _principled(mat):
    if mat.node_tree is None:               # Blender < 5 needs use_nodes; 5.x always has a tree
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None) or nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return bsdf


def material(name):
    """Named project material from style.json ('MAT_Cream', ...). Created once, then reused."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    spec = style()["materials"][name]
    return pbr(name, spec["color"], spec.get("roughness", 0.5), spec.get("metallic", 0.0))


def pbr(name, color, roughness=0.5, metallic=0.0):
    """Asset-specific plain material. `name` must start with MAT_ or the asset prefix (XB_, GG_ ...)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    mat.diffuse_color = rgba(color)        # viewport / workbench color
    return mat


def emissive(name, color, strength=None, base="screen_off"):
    """Glowing material (screens, bulbs, neon)."""
    mat = pbr(name, base, 0.3, 0.0)
    bsdf = _principled(mat)
    key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
    bsdf.inputs[key].default_value = rgba(color)
    bsdf.inputs["Emission Strength"].default_value = style()["face"]["emission_strength"] if strength is None else strength
    return mat


def assign(obj, mat):
    if obj.data is not None and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


# --------------------------------------------------------------------------- primitives
def _finish(obj, name, mat, col, smooth=True):
    obj.name = name
    if obj.data is not None:
        obj.data.name = name
    if mat is not None:
        assign(obj, mat)
    if col is not None:
        move_to(obj, col)
    if smooth and obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def add_bevel(obj, width=0.02, segments=3):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    return m


def add_subsurf(obj, viewport=1, render=2):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = viewport
    m.render_levels = render
    return m


def rounded_box(name, size, location, mat=None, bevel=0.02, segments=3, subsurf=1,
                rotation=(0, 0, 0), col=None):
    """Box of `size` (x, y, z) meters centered at `location`, with bevel (+ optional subsurf).
    Scale is applied, so the object scale stays (1, 1, 1)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        add_bevel(obj, bevel, segments)
    if subsurf:
        add_subsurf(obj, 1, subsurf)
    return _finish(obj, name, mat, col)


def cylinder(name, radius, depth, location, mat=None, vertices=48, bevel=0.0,
             rotation=(0, 0, 0), col=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=vertices,
                                        location=location, rotation=rotation)
    obj = bpy.context.active_object
    if bevel:
        add_bevel(obj, bevel, 3)
    return _finish(obj, name, mat, col)


def sphere(name, radius, location, mat=None, segments=48, rings=24, col=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments, ring_count=rings,
                                         location=location)
    obj = bpy.context.active_object
    return _finish(obj, name, mat, col)


def plane(name, size_xy, location, mat=None, rotation=(0, 0, 0), col=None):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.scale = (size_xy[0], size_xy[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(obj, name, mat, col, smooth=False)


# --------------------------------------------------------------------------- custom properties
def add_prop(idblock, name, default, minimum=None, maximum=None, description="", subtype=None):
    """Animatable custom property with UI limits (the pipeline keyframes these).
    Colors: pass a 3-float list of LINEAR RGB (use C.rgb('teal')) and subtype='COLOR'."""
    idblock[name] = default
    ui = idblock.id_properties_ui(name)
    kw = {"description": description}
    if minimum is not None:
        kw["min"] = minimum
        kw["soft_min"] = minimum
    if maximum is not None:
        kw["max"] = maximum
        kw["soft_max"] = maximum
    if subtype:
        kw["subtype"] = subtype
    ui.update(**kw)
    idblock.property_overridable_library_set(f'["{name}"]', True)
    return name


def drive(target, data_path, source_obj, source_prop, expression="v", index=-1, source_index=None):
    """Driver: target.data_path[index] <- expression(v), where v = source_obj["source_prop"]
    (or source_obj["source_prop"][source_index] for vector props such as face_color).
    `target` can be an ID or any struct with driver_add (pose bone, node socket ...).
    Example (face color channel 0 -> emission socket):
        sock = mat.node_tree.nodes["Emission"].inputs["Color"]
        C.drive(sock, "default_value", rig, "face_color", index=0, source_index=0)
    """
    fc = target.driver_add(data_path, index) if index >= 0 else target.driver_add(data_path)
    if isinstance(fc, (list, tuple)):          # vector path without index -> drive every channel
        return [drive(target, data_path, source_obj, source_prop, expression, i,
                      i if source_index == "each" else source_index) for i in range(len(fc))]
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "v"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"
    var.targets[0].id = source_obj
    path = f'["{source_prop}"]'
    if source_index is not None:
        path += f"[{source_index}]"
    var.targets[0].data_path = path
    drv.expression = expression
    return fc


# --------------------------------------------------------------------------- measurement
def collection_objects(col_name):
    col = bpy.data.collections[col_name]
    return list(col.all_objects)


def triangles(objects, render_levels=True):
    """Triangle count of evaluated meshes. With render_levels, subsurf uses its render level."""
    saved = []
    if render_levels:
        for o in objects:
            if o.library is not None or (o.override_library and o.override_library.is_system_override):
                continue                         # linked / system-override data is read-only
            for m in getattr(o, "modifiers", []):
                if m.type == "SUBSURF":
                    try:
                        lv = m.levels
                        m.levels = m.render_levels
                        saved.append((m, lv))
                    except (AttributeError, RuntimeError):
                        pass
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    total = 0
    for o in objects:
        if o.type not in {"MESH", "CURVE", "FONT", "SURFACE", "META"}:
            continue
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is not None:
            me.calc_loop_triangles()
            total += len(me.loop_triangles)
            ev.to_mesh_clear()
    for m, lv in saved:
        try:
            m.levels = lv
        except (AttributeError, RuntimeError):
            pass
    return total


def world_bbox(objects):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objects:
        if o.type in {"MESH", "CURVE", "FONT", "SURFACE", "META"}:
            ev = o.evaluated_get(dg)
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    if not pts:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


# --------------------------------------------------------------------------- render
def eevee_id():
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    return "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE"


def setup_render(scene=None, preview=False, resolution=None):
    sc = scene or bpy.context.scene
    r = style()["render"]
    sc.render.engine = eevee_id()
    w, h = resolution or (r["preview_resolution"] if preview else r["resolution"])
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.fps = r["fps"]
    sc.eevee.taa_render_samples = r["samples_preview"] if preview else r["samples_final"]
    sc.render.image_settings.file_format = r["file_format"]
    try:
        sc.view_settings.view_transform = r["view_transform"]
    except TypeError:
        pass
    return sc


def render_still(path, scene=None):
    sc = scene or bpy.context.scene
    p = abspath(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(p)
    bpy.ops.render.render(write_still=True)
    return p


def _look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def studio_preview(col_name, out_dir, prefix=None, size=900):
    """Render front / three-quarter / side / top-three-quarter previews of a collection with a
    neutral 3-point light rig. The rig lives in a temporary collection that is deleted afterwards,
    so call this AFTER save() (or the rig would be saved into the asset)."""
    sc = bpy.context.scene
    objs = collection_objects(col_name)
    mn, mx = world_bbox(objs)
    center = (mn + mx) / 2
    radius = max((mx - mn).length / 2, 0.05)
    rig = collection("_PREVIEW_RIG")
    floor = plane("_PV_Floor", (radius * 20, radius * 20), (center.x, center.y, mn.z - 0.001),
                  pbr("_PV_FloorMat", "#3A3A3A", 0.8), col=rig)
    cam_data = bpy.data.cameras.new("_PV_Cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("_PV_Cam", cam_data)
    rig.objects.link(cam)
    sc.camera = cam
    lights = []
    for nm, off, energy in (("_PV_Key", (-1.2, -1.6, 1.4), 300), ("_PV_Fill", (1.6, -1.0, 0.6), 90),
                            ("_PV_Rim", (0.6, 1.8, 1.5), 200)):
        ld = bpy.data.lights.new(nm, "AREA")
        ld.energy = energy * (radius / 0.5) ** 2
        ld.size = radius * 1.5
        lo = bpy.data.objects.new(nm, ld)
        lo.location = center + Vector(off) * radius * 3
        rig.objects.link(lo)
        _look_at(lo, center)
        lights.append(lo)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("_PV_World")
    if sc.world.node_tree is None:
        sc.world.use_nodes = True
    bg = next((n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg:
        bg.inputs[0].default_value = (0.03, 0.03, 0.035, 1)
    setup_render(sc, preview=True, resolution=(size, size))
    dist = radius / math.tan(math.atan(18 / 50)) * 1.25
    views = {"front": (0, -1, 0.15), "threequarter": (0.75, -1, 0.35), "side": (1, 0, 0.15),
             "top": (0.5, -0.7, 1.1)}
    prefix = prefix or col_name
    outs = []
    for vname, d in views.items():
        dv = Vector(d).normalized()
        cam.location = center + dv * dist
        _look_at(cam, center)
        outs.append(str(render_still(f"{out_dir}/{prefix}_{vname}.png", sc)))
    # clean up the temporary rig
    for o in list(rig.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(rig)
    return outs


# --------------------------------------------------------------------------- save
def save(rel_path, compress=True):
    p = abspath(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(p), compress=compress, relative_remap=True)
    print(f"[common] saved {p}")
    return p
