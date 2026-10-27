// PNG + GLB export.
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

export function exportPNG(renderer, scene, camera, filename = 'form-01.png') {
  renderer.render(scene, camera);
  return new Promise((resolve, reject) => {
    renderer.domElement.toBlob((blob) => {
      if (!blob) return reject(new Error('PNG encoding failed'));
      download(blob, filename);
      resolve({ bytes: blob.size, filename });
    }, 'image/png');
  });
}

export function exportGLB(modelRoot, filename = 'form-01.glb') {
  return new Promise((resolve, reject) => {
    // manual clone: transforms + shared geometry/materials only (internal userData is circular)
    const cloneTree = (src) => {
      const out = src.isMesh ? new src.constructor(src.geometry, src.material) : new THREE.Group();
      out.name = src.name;
      out.position.copy(src.position);
      out.quaternion.copy(src.quaternion);
      out.scale.copy(src.scale);
      out.visible = src.visible;
      for (const c of src.children) out.add(cloneTree(c));
      return out;
    };
    const clone = cloneTree(modelRoot);
    const exporter = new GLTFExporter();
    exporter.parse(
      clone,
      (buf) => {
        const blob = new Blob([buf], { type: 'model/gltf-binary' });
        download(blob, filename);
        resolve({ bytes: blob.size, filename });
      },
      (err) => reject(err instanceof Error ? err : new Error(String(err))),
      { binary: true, onlyVisible: true },
    );
  });
}

function download(blob, filename) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800);
}
