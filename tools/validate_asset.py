"""Validate a built .blend against its interface contract (contracts/*.json).

    tools/validate.sh assets/xiaobo.blend contracts/xiaobo.json
    (= Blender -b <blend> -P tools/validate_asset.py -- --contract <json> [--no-render])

Checks: collections, objects + types, bones, custom properties + ranges, actions, material
naming and nodes, drivers, parenting to the root, triangle budget (render subdivision),
bounding-box size (measured at frame 1 with the saved active action), origin on floor, missing
external files, negative scale. Writes tasks/reports/validation/<asset>/report.json + report.md, renders
previews (studio previews for assets, one still per camera for the room).
Exit code 0 = PASS, 1 = FAIL.
"""
import bpy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets" / "build"))
import _common as C  # noqa: E402


def parse_args():
    a = C.argv()
    opts = {"contract": None, "render": True, "report_dir": None}
    i = 0
    while i < len(a):
        if a[i] == "--contract":
            opts["contract"] = a[i + 1]
            i += 2
        elif a[i] == "--report-dir":
            opts["report_dir"] = a[i + 1]
            i += 2
        elif a[i] == "--no-render":
            opts["render"] = False
            i += 1
        else:
            i += 1
    if not opts["contract"]:
        raise SystemExit("usage: ... -- --contract contracts/<asset>.json [--no-render]")
    return opts


class Report:
    def __init__(self, asset):
        self.asset = asset
        self.errors, self.warnings, self.info = [], [], {}

    def err(self, msg):
        self.errors.append(msg)
        print("[validate] ERROR", msg)

    def warn(self, msg):
        self.warnings.append(msg)
        print("[validate] WARN ", msg)


def check(contract, rep):
    bpy.context.scene.frame_set(1)
    col_name = contract["collection"]
    col = bpy.data.collections.get(col_name)
    if col is None:
        rep.err(f"collection '{col_name}' missing")
        return []
    objs = list(col.all_objects)
    names = {o.name: o for o in objs}

    for sub in contract.get("sub_collections", []):
        if bpy.data.collections.get(sub) is None:
            rep.err(f"sub-collection '{sub}' missing")

    for spec in contract.get("objects", []):
        o = names.get(spec["name"])
        if o is None:
            rep.err(f"object '{spec['name']}' missing from collection '{col_name}'")
            continue
        if "type" in spec and o.type != spec["type"]:
            rep.err(f"object '{o.name}' type {o.type}, expected {spec['type']}")

    for arm_name, bones in contract.get("bones", {}).items():
        arm = bpy.data.objects.get(arm_name)
        if arm is None or arm.type != "ARMATURE":
            rep.err(f"armature '{arm_name}' missing")
            continue
        for b in bones:
            if b not in arm.data.bones:
                rep.err(f"bone '{b}' missing in '{arm_name}'")

    for p in contract.get("custom_props", []):
        o = bpy.data.objects.get(p["object"])
        if o is None:
            rep.err(f"custom prop owner '{p['object']}' missing")
            continue
        if p["name"] not in o.keys():
            rep.err(f"custom prop '{p['object']}[\"{p['name']}\"]' missing")
            continue
        ui = o.id_properties_ui(p["name"]).as_dict()
        for k in ("min", "max"):
            if k in p and ui.get(k) is not None and abs(float(ui[k]) - float(p[k])) > 1e-6:
                rep.err(f"custom prop '{p['object']}[\"{p['name']}\"]' {k}={ui.get(k)}, expected {p[k]}")

    for a in contract.get("actions", []):
        act = bpy.data.actions.get(a)
        if act is None:
            rep.err(f"action '{a}' missing")
        elif not (act.use_fake_user or act.users > 0):
            rep.err(f"action '{a}' has no users and no fake user (would not be saved)")

    for n in contract.get("cameras", []):
        o = bpy.data.objects.get(n)
        if o is None or o.type != "CAMERA":
            rep.err(f"camera '{n}' missing")
    for n in contract.get("lights", []):
        o = bpy.data.objects.get(n)
        if o is None or o.type != "LIGHT":
            rep.err(f"light '{n}' missing")
    for n in contract.get("marks", []):
        if bpy.data.objects.get(n) is None:
            rep.err(f"mark '{n}' missing")

    prefixes = tuple(contract.get("material_prefixes", ["MAT_"]))
    used = {m.name for o in objs for m in getattr(getattr(o, "data", None), "materials", []) if m}
    for m in sorted(used):
        if not m.startswith(prefixes):
            rep.err(f"material '{m}' does not start with {prefixes}")
    rep.info["materials"] = sorted(used)

    for spec in contract.get("material_nodes", []):
        mat = bpy.data.materials.get(spec["material"])
        if mat is None or mat.node_tree is None:
            rep.err(f"material '{spec['material']}' missing")
            continue
        node = mat.node_tree.nodes.get(spec["node"])
        if node is None:
            rep.err(f"node '{spec['node']}' missing in material '{spec['material']}'")
        elif "type" in spec and node.type != spec["type"]:
            rep.err(f"node '{spec['node']}' type {node.type}, expected {spec['type']}")

    for spec in contract.get("drivers_required", []):
        # Drivers may live on the object, on its data (light color, shape keys) or on its
        # materials' node trees; count all of them.
        o = bpy.data.objects.get(spec["object"])
        holders = []
        if o is not None:
            holders.append(o)
            if o.data is not None:
                holders.append(o.data)
                sk = getattr(o.data, "shape_keys", None)
                if sk is not None:
                    holders.append(sk)
                for m in getattr(o.data, "materials", []) or []:
                    if m is not None and m.node_tree is not None:
                        holders.append(m.node_tree)
            if o.data is not None and getattr(o.data, "node_tree", None) is not None:
                holders.append(o.data.node_tree)      # light / world node trees
        else:
            m = bpy.data.materials.get(spec["object"])
            if m is not None and m.node_tree is not None:
                holders.append(m.node_tree)
        n = sum(len(h.animation_data.drivers) for h in holders if getattr(h, "animation_data", None))
        if not holders:
            rep.err(f"driver owner '{spec['object']}' missing")
        elif n < spec.get("min", 1):
            rep.err(f"'{spec['object']}' has {n} drivers, expected at least {spec.get('min', 1)}")

    # every part must hang under the root, because T08 only moves the root
    def descends(o, root):
        p = o.parent
        while p is not None:
            if p == root:
                return True
            p = p.parent
        return False
    root = bpy.data.objects.get(contract.get("root", ""))
    if root is not None:
        for o in objs:
            if o != root and not descends(o, root):
                rep.err(f"object '{o.name}' is not parented (directly or indirectly) to root '{root.name}'")
    if contract.get("per_subcollection_root"):
        for sub in contract.get("sub_collections", []):
            sc = bpy.data.collections.get(sub)
            r = bpy.data.objects.get(sub)
            if sc is None or r is None:
                continue
            for o in sc.all_objects:
                if o != r and not descends(o, r):
                    rep.err(f"object '{o.name}' in '{sub}' is not parented to '{sub}'")

    # drivers: invalid ones are errors; non-simple Python expressions only work with auto-run enabled
    seen = set()
    for idb in list(bpy.data.objects) + list(bpy.data.materials) + list(bpy.data.lights) + list(bpy.data.shape_keys):
        holders = [idb] + ([idb.node_tree] if getattr(idb, "node_tree", None) is not None else [])
        for h in holders:
            ad = getattr(h, "animation_data", None)
            if not ad:
                continue
            for fc in ad.drivers:
                key = (h.name, fc.data_path, fc.array_index)
                if key in seen:
                    continue
                seen.add(key)
                if not fc.is_valid or not fc.driver.is_valid:
                    rep.err(f"invalid driver on '{h.name}': {fc.data_path}[{fc.array_index}]")
                elif fc.driver.type == "SCRIPTED" and not fc.driver.is_simple_expression:
                    rep.warn(f"driver on '{h.name}' {fc.data_path}[{fc.array_index}] is not a simple expression "
                             f"('{fc.driver.expression}'); it needs Python auto-run. Prefer a simple expression.")

    tris = C.triangles(objs, render_levels=True)
    rep.info["triangles_render"] = tris
    if "max_triangles" in contract and tris > contract["max_triangles"]:
        rep.err(f"triangles {tris} > budget {contract['max_triangles']}")

    mn, mx = C.world_bbox(objs)
    size = [round(v, 4) for v in (mx - mn)]
    rep.info["bbox_min"] = [round(v, 4) for v in mn]
    rep.info["bbox_size"] = size
    bb = contract.get("bbox")
    if bb:
        for i, axis in enumerate("xyz"):
            if size[i] < bb["min_size"][i] - 1e-4 or size[i] > bb["max_size"][i] + 1e-4:
                rep.err(f"bbox {axis} size {size[i]} outside [{bb['min_size'][i]}, {bb['max_size'][i]}]")
    if contract.get("origin_on_floor"):
        if abs(mn.z) > 0.01:
            rep.err(f"lowest point z={mn.z:.4f}, expected ~0 (asset must stand on z=0)")
        root = bpy.data.objects.get(contract.get("root", ""))
        if root is not None and root.location.length > 1e-4:
            rep.err(f"root '{root.name}' at {tuple(round(v, 4) for v in root.location)}, expected origin")

    for o in objs:
        if any(s < 0 for s in o.scale):
            rep.err(f"object '{o.name}' has negative scale")
    for img in bpy.data.images:
        if img.source in {"FILE", "SEQUENCE", "MOVIE"} and not img.packed_file:
            fp = Path(bpy.path.abspath(img.filepath, library=img.library))
            if img.filepath and not fp.exists():
                rep.err(f"image '{img.name}' file missing: {img.filepath}")
    return objs


def main():
    opts = parse_args()
    contract = json.load(open(C.abspath(opts["contract"]), encoding="utf-8"))
    rep = Report(contract["asset"])
    t0 = time.time()
    check(contract, rep)
    out_dir = opts["report_dir"] or f"tasks/reports/validation/{contract['asset']}"
    previews = []
    if opts["render"] and not rep.errors:
        if contract.get("render_cameras"):
            sc = bpy.context.scene
            C.setup_render(sc, preview=True)
            for cam in contract.get("cameras", []):
                sc.camera = bpy.data.objects[cam]
                previews.append(str(C.render_still(f"{out_dir}/{cam}.png", sc)))
        else:
            previews = C.studio_preview(contract["collection"], out_dir, contract["asset"])
    result = {
        "asset": contract["asset"], "blend": bpy.data.filepath, "blender": bpy.app.version_string,
        "status": "PASS" if not rep.errors else "FAIL", "errors": rep.errors,
        "warnings": rep.warnings, "info": rep.info, "previews": previews,
        "seconds": round(time.time() - t0, 1),
    }
    out = C.abspath(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Validation: {contract['asset']} — {result['status']}", "",
          f"- blend: `{result['blend']}`", f"- Blender: {result['blender']}",
          f"- triangles (render): {rep.info.get('triangles_render')}",
          f"- bbox size (m): {rep.info.get('bbox_size')}", ""]
    md += ["## Errors"] + [f"- {e}" for e in rep.errors or ["none"]] + [""]
    md += ["## Warnings"] + [f"- {w}" for w in rep.warnings or ["none"]] + [""]
    md += ["## Previews"] + [f"- `{p}`" for p in previews or ["(not rendered)"]]
    (out / "report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[validate] {result['status']}  report: {out / 'report.md'}")
    sys.exit(0 if not rep.errors else 1)


main()
