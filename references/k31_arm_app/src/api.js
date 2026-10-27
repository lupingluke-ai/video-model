// window.__rebuild — public scripting and UI API.
import * as THREE from 'three';
import { SKINS } from './materials.js';
import { MODES } from './modes.js';
import { GESTURES, ARM_POSES } from './pose.js?v=short-20261012';
import { exportPNG, exportGLB } from './exporter.js';
import { describePart } from './parts-info.js';

export function createAPI(ctx) {
  const { model, pose, modes, materials, wiring, scene, camera, renderer, controls } = ctx;

  const api = {
    model, scene, camera, renderer,
    armJointInfo: pose.armJointInfo,
    handJointInfo: pose.handJointInfo,
    skins: Object.keys(SKINS),
    modes: MODES,
    gestures: [...Object.keys(GESTURES), 'ripple', 'wave'],
    armPoses: Object.keys(ARM_POSES),
    ui: null, // set by main when initUI resolves

    setMode(mode) { modes.set(mode); modes.snapBlend(); api._changed(); },
    setShellBlend(p, o) { modes.setBlend(p, o); api._changed(); },
    setSkin(id) {
      if (!SKINS[id]) return;
      materials.applySkin(id, api._shellDepth);
      api._changed();
    },
    setShellDepth(d) {
      api._shellDepth = Math.min(1, Math.max(0, Number(d)));
      materials.applySkin(materials.skinId, api._shellDepth);
      api._changed();
    },
    setGesture(name) { pose.setGesture(name); api._changed(); },
    setPose(name) {
      if (ARM_POSES[name]) pose.setArmPose(name);
      else if (GESTURES[name] || name === 'ripple' || name === 'wave') pose.setGesture(name);
      api._changed();
    },
    setArmAngles(deg) { pose.setArmAngles(deg); api._renderOnce(); },
    setHandAngles(deg) { pose.setHandAngles(deg); api._renderOnce(); },
    setHandCurl(v) { pose.setHandCurl(v); api._renderOnce(); },
    setPlaying(b) { pose.setPlaying(b); api._changed(); },
    setTime(t) { pose.setTime(t); api._renderOnce(); },
    setSectionOffset(v) { modes.setSectionOffset(v); api._renderOnce(); },

    focus(part) { ctx.focusPart(part); },

    render() { api._renderOnce(); },

    applyReferenceFrame(f) {
      pose.cancelMotion();
      modes.set(f.mode === 'open' ? 'open' : 'transparent');
      modes.snapBlend();
      materials.applySkin(f.skin || 'frost', 1);
      api.setIsolate(!!f.isolate);
      pose.setArmAngles(f.armAngles_deg.map(a => a.angle));
      pose.setHandAngles(f.handAngles_deg.map(a => a.angle));
      // exact reference render size (1024x1024) and camera transform
      const w = f.width || 1024, h = f.height || 1024;
      renderer.setPixelRatio(1);
      renderer.setSize(w, h, false);
      const cam = f.camera;
      camera.fov = cam.fov_y_deg;
      camera.near = cam.near;
      camera.far = cam.far;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      const m = new THREE.Matrix4().fromArray(cam.worldMatrix_columnMajor);
      m.decompose(camera.position, camera.quaternion, new THREE.Vector3());
      camera.quaternion.setFromRotationMatrix(m);
      controls.enabled = false;
      api._renderOnce();
    },

    getLandmarks() { return model.getLandmarks(); },

    setIsolate(on) {
      api._isolate = !!on;
      modes.setIsolate(on);
      api._renderOnce();
    },

    setMaskMode(on) {
      if (on) {
        scene.overrideMaterial = materials.maskMat;
        api._bgSaved = scene.background;
        scene.background = new THREE.Color('#ffffff');
        ctx.env.floor.visible = false;
        ctx.env.contact.visible = false;
      } else {
        scene.overrideMaterial = null;
        scene.background = api._bgSaved;
        ctx.env.floor.visible = true;
        ctx.env.contact.visible = true;
      }
      api._renderOnce();
    },

    exportPNG() { return exportPNG(renderer, scene, camera, 'form-01-view.png'); },
    exportGLB() { return exportGLB(model.root, 'form-01.glb'); },

    describePart,

    snapshot() {
      let meshCount = 0;
      scene.traverse(o => { if (o.isMesh && o.visible) meshCount++; });
      return {
        mode: modes.mode,
        skin: materials.skinId,
        gesture: pose.gesture,
        playing: pose.playing,
        armAngles: [...pose.armAngles],
        handAngles: [...pose.handAngles],
        time: pose.time,
        shellDepth: api._shellDepth,
        curl: pose.curl,
        blend: modes.blend,
        story: api.story ? api.story.getState() : null,
        stats: {
          meshCount,
          partCount: model.buckets.reduce((a, b) => a + b.parts.length, 0),
          wireCount: (wiring.count || 0) + (model.staticWireCount || 0),
          dynamicWireCount: wiring.count || 0,
        },
      };
    },

    // internal helpers
    _shellDepth: 1,
    _isolate: false,
    _changed() { ctx.onStateChange?.(api.snapshot()); },
    _renderOnce() {
      pose.flush();
      renderer.render(scene, camera);
      api._changed();
    },
  };

  return api;
}
