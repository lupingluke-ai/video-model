"""Environment self-test (task T00). Run (use your task id as tag so parallel agents don't collide):
    bash tools/blender.sh tools/selftest.py --tag T02
or, from Blender's Python console:
    import subprocess,os; d=os.path.expanduser('~/Documents/personal/video-model'); subprocess.Popen([bpy.app.binary_path,'-b','--factory-startup','-P',d+'/tools/selftest.py'])
It builds a tiny asset with _common, saves it, renders studio previews, then runs the
validator on it in a second headless Blender. Result: tests/results/selftest_<tag>.json
"""
import bpy, json, platform, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets" / "build"))
import _common as C

a = C.argv()
TAG = a[a.index("--tag") + 1] if "--tag" in a else "default"
res = {"blender": bpy.app.version_string, "platform": platform.platform(), "tag": TAG, "steps": {}}
out = ROOT / "tests" / "results"
out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
try:
    C.reset_scene()
    col = C.collection("ST")
    root = C.empty("ST_Root", (0, 0, 0), col)
    box = C.rounded_box("ST_Box", (0.3, 0.25, 0.3), (0, 0, 0.15), C.material("MAT_Cream"), bevel=0.04, col=col)
    scr = C.rounded_box("ST_Screen", (0.2, 0.01, 0.12), (0, -0.128, 0.18), C.emissive("ST_Face", "teal"), bevel=0.01, subsurf=0, col=col)
    C.set_parent(box, root); C.set_parent(scr, root)
    C.add_prop(scr, "mouth_open", 0.0, 0.0, 1.0, "0 closed .. 1 open")
    C.add_prop(scr, "face_color", list(C.rgb("teal")), subtype="COLOR")
    mat = scr.data.materials[0]
    img = mat.node_tree.nodes.new("ShaderNodeTexImage"); img.name = "ST_Img"
    ld = bpy.data.lights.new("ST_Light", "POINT"); lo = bpy.data.objects.new("ST_Light", ld)
    col.objects.link(lo); lo.location = (0, -0.3, 0.2); C.set_parent(lo, root)
    for i in range(3):
        C.drive(ld, "color", scr, "face_color", index=i, source_index=i)
    C.drive(ld, "energy", scr, "mouth_open", expression="5 + 20*v")
    res["steps"]["build"] = "ok"
    res["triangles"] = C.triangles(C.collection_objects("ST"))
    bpy.context.view_layer.update()
    lw = lo.matrix_world.translation; bw = box.matrix_world.translation
    assert (lw - __import__("mathutils").Vector((0, -0.3, 0.2))).length < 1e-4, f"light at {tuple(lw)}"
    assert abs(bw.z - 0.15) < 1e-4, f"box at {tuple(bw)}"
    res["steps"]["parenting"] = "ok"
    blend = f"tests/selftest/{TAG}/selftest.blend"
    C.save(blend)
    res["steps"]["save"] = "ok"
    t1 = time.time()
    res["previews"] = C.studio_preview("ST", f"tests/results/selftest_{TAG}_previews")
    res["preview_seconds"] = round(time.time() - t1, 2)
    res["steps"]["preview"] = "ok"
    v = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", str(ROOT / blend),
                        "--python-exit-code", "1", "-P", str(ROOT / "tools/validate_asset.py"), "--",
                        "--contract", "contracts/_selftest.json",
                        "--report-dir", f"tests/results/selftest_{TAG}_validation"],
                       capture_output=True, text=True, timeout=600)
    res["validate_exit"] = v.returncode
    res["validate_tail"] = v.stdout[-1500:]
    res["steps"]["validate"] = "ok" if v.returncode == 0 else "FAIL"
except Exception as e:
    import traceback
    res["error"] = traceback.format_exc()
res["seconds"] = round(time.time() - t0, 1)
res["status"] = "PASS" if all(s == "ok" for s in res["steps"].values()) and len(res["steps"]) == 5 else "FAIL"
(out / f"selftest_{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print("[selftest]", res["status"])
