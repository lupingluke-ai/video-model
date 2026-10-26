"""Blender benchmark for the 小波深夜电台 pipeline.
Run headless:  blender -b --factory-startup -P tests/bench.py
Builds a representative stylised room (rounded props, emissive screen face,
practical lights, optional volume fog, DOF) and times renders for several
engine/quality configs. Writes tests/results/bench.json + sample PNGs.
Works on Blender 4.2+ and 5.x."""
import bpy, bmesh, math, time, json, os, sys, platform, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OUT, "bench_progress.txt")

def log(msg):
    print("[bench]", msg, flush=True)
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + str(msg) + "\n")

def hexcol(h, a=1.0):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), a)

def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hexcol(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[key].default_value = hexcol(emit)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m

def rounded(name, size, loc, m, bevel=0.03, subsurf=2, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bv = o.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 3
    if subsurf:
        ss = o.modifiers.new("sub", "SUBSURF"); ss.levels = 1; ss.render_levels = subsurf
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    P = dict(walnut=mat("walnut", "#4A2F1D", 0.55), olive=mat("olive", "#3F4A3A", 0.8),
             orange=mat("orange", "#C8612B", 0.45), mustard=mat("mustard", "#D4A62A", 0.5),
             cream=mat("cream", "#EDE0C4", 0.5), brass=mat("brass", "#B08D57", 0.3, 1.0),
             screen=mat("screen", "#0A0F0E", 0.3, 0, "#4FE3C1", 6.0),
             lamp=mat("lamp", "#EDE0C4", 0.4, 0, "#FFB36B", 8.0))
    # room shell 5 x 4 x 2.7
    rounded("floor", (5, 4, 0.1), (0, 0, -0.05), P["walnut"], 0.01, 0)
    rounded("wall_back", (5, 0.1, 2.7), (0, 2, 1.35), P["olive"], 0.01, 0)
    rounded("wall_left", (0.1, 4, 2.7), (-2.5, 0, 1.35), P["walnut"], 0.01, 0)
    for i in range(24):  # slat wall
        rounded(f"slat_{i}", (0.05, 0.04, 2.5), (-2.3 + i * 0.09, 1.93, 1.3), P["walnut"], 0.01, 0)
    # furniture
    rounded("sofa_base", (1.8, 0.8, 0.4), (-1.2, 1.2, 0.2), P["orange"], 0.08)
    rounded("sofa_back", (1.8, 0.25, 0.5), (-1.2, 1.55, 0.6), P["orange"], 0.08)
    rounded("desk", (1.2, 0.6, 0.08), (0.6, 0.3, 0.7), P["walnut"], 0.02)
    for x in (0.1, 1.1):
        rounded(f"desk_leg_{x}", (0.06, 0.06, 0.7), (x, 0.3, 0.35), P["brass"], 0.01, 0)
    rounded("workbench", (1.0, 0.6, 0.9), (1.9, 1.4, 0.45), P["walnut"], 0.02)
    rounded("tv", (0.6, 0.45, 0.5), (1.9, 1.5, 1.15), P["walnut"], 0.06)
    rounded("tv_screen", (0.48, 0.02, 0.36), (1.9, 1.26, 1.15), P["screen"], 0.03, 1)
    # robot (xiaobo) proxy: capsule head + body + screen face
    rounded("xb_body", (0.35, 0.3, 0.45), (0.6, -0.2, 0.95), P["cream"], 0.12)
    rounded("xb_head", (0.5, 0.3, 0.3), (0.6, -0.2, 1.38), P["cream"], 0.14)
    rounded("xb_face", (0.36, 0.02, 0.2), (0.6, -0.36, 1.38), P["screen"], 0.06, 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.3, location=(0.75, -0.2, 1.65))
    bpy.context.active_object.data.materials.append(P["brass"])
    # pet proxy
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(-0.3, -0.6, 0.15), segments=48, ring_count=24)
    o = bpy.context.active_object; o.data.materials.append(P["mustard"]); bpy.ops.object.shade_smooth()
    # flipchart proxy
    rounded("flip_paper", (0.7, 0.03, 0.9), (-0.9, -0.1, 1.2), P["cream"], 0.01, 0)
    # practical lamps
    for i, (x, y, z) in enumerate([(-2.1, 1.6, 1.5), (0.1, 0.5, 1.0), (2.3, 1.7, 1.9)]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, z))
        g = bpy.context.active_object; g.data.materials.append(P["lamp"]); bpy.ops.object.shade_smooth()
        bpy.ops.object.light_add(type='POINT', location=(x, y, z))
        L = bpy.context.active_object.data; L.energy = 60; L.color = (1.0, 0.72, 0.45); L.shadow_soft_size = 0.15
    # key / rim / face light
    bpy.ops.object.light_add(type='AREA', location=(2.0, -2.5, 2.2), rotation=(math.radians(60), 0, math.radians(40)))
    k = bpy.context.active_object.data; k.energy = 250; k.size = 1.5; k.color = (1.0, 0.85, 0.7)
    bpy.ops.object.light_add(type='AREA', location=(-1.5, 2.6, 2.0), rotation=(math.radians(-60), 0, math.radians(200)))
    r = bpy.context.active_object.data; r.energy = 120; r.size = 1.0; r.color = (0.55, 0.7, 1.0)
    bpy.ops.object.light_add(type='AREA', location=(0.6, -0.45, 1.38), rotation=(math.radians(-90), 0, 0))
    f = bpy.context.active_object.data; f.energy = 8; f.size = 0.3; f.color = hexcol("#4FE3C1")[:3]
    # world
    w = bpy.data.worlds.new("world"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.02, 1)
    # fog volume (toggled per config)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.35)); fog = bpy.context.active_object
    fog.name = "fog"; fog.scale = (4.9, 3.9, 2.6)
    fm = bpy.data.materials.new("fog"); fm.use_nodes = True; nt = fm.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 0.03
    nt.links.new(pv.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    fog.data.materials.append(fm)
    # camera with DOF on the robot
    bpy.ops.object.camera_add(location=(0.9, -2.6, 1.35), rotation=(math.radians(88), 0, math.radians(6)))
    cam = bpy.context.active_object; sc.camera = cam
    cam.data.lens = 40; cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 2.4; cam.data.dof.aperture_fstop = 2.8
    return sc, fog

def eevee_id():
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    return 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in ids else 'BLENDER_EEVEE'

def setup_gpu_cycles():
    info = {}
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for t in ('METAL', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
            try:
                prefs.compute_device_type = t; prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == t]
                if devs:
                    for d in prefs.devices: d.use = (d.type == t)
                    info = {"type": t, "devices": [d.name for d in devs]}
                    break
            except Exception:
                continue
    except Exception as e:
        info = {"error": str(e)}
    return info

def render_once(sc, path):
    sc.render.filepath = path
    t0 = time.time(); bpy.ops.render.render(write_still=True); return round(time.time() - t0, 2)

def main():
    open(LOG, "w").close()
    log(f"Blender {bpy.app.version_string} on {platform.platform()} background={bpy.app.background}")
    sc, fog = build_scene()
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in sc.objects:
        if o.type == 'MESH':
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    log(f"scene triangles (render-level eval) ~{tris}")
    sc.render.image_settings.file_format = 'PNG'
    results = {"blender": bpy.app.version_string, "platform": platform.platform(),
               "machine": platform.machine(), "background": bpy.app.background,
               "scene_triangles": tris, "runs": []}
    gpu = setup_gpu_cycles(); results["cycles_gpu"] = gpu; log(f"cycles gpu: {gpu}")
    E = eevee_id()
    configs = [
        ("eevee_preview_540p", E, 960, 540, 16, False),
        ("eevee_1080p_s32", E, 1920, 1080, 32, False),
        ("eevee_1080p_s64_fog", E, 1920, 1080, 64, True),
        ("cycles_gpu_1080p_s64_denoise", 'CYCLES', 1920, 1080, 64, True),
    ]
    for name, eng, w, h, samples, use_fog in configs:
        try:
            sc.render.engine = eng; sc.render.resolution_x = w; sc.render.resolution_y = h
            sc.render.resolution_percentage = 100
            fog.hide_render = not use_fog
            if eng == 'CYCLES':
                sc.cycles.device = 'GPU' if gpu.get("devices") else 'CPU'
                sc.cycles.samples = samples; sc.cycles.use_denoising = True
            else:
                sc.eevee.taa_render_samples = samples
            first = render_once(sc, os.path.join(OUT, f"{name}_a.png"))
            second = render_once(sc, os.path.join(OUT, f"{name}_b.png"))
            run = {"name": name, "engine": eng, "res": f"{w}x{h}", "samples": samples, "fog": use_fog,
                   "first_s": first, "steady_s": second}
            results["runs"].append(run); log(run)
        except Exception as e:
            results["runs"].append({"name": name, "error": repr(e)}); log(f"{name} FAILED {e!r}")
        with open(os.path.join(OUT, "bench.json"), "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "bench_scene.blend"))
    log("DONE")

main()
