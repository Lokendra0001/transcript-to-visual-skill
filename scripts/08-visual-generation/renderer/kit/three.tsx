// Three.js integration: genuine 3D (materials, lighting, reflections, glass, soft shadows) for
// elements SVG and Zdog cannot reproduce. Rendered offscreen with WebGL (SwiftShader in headless
// Chrome), transparent background preserved, embedded as a PNG data URI <image>. It is the one
// raster technology in the kit: the renderer lists every such image under `rasters` and fails the
// run when its pixel density is below the PNG capture scale. Use only when the plan justifies it.
import { useMemo } from 'react';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { renderScale } from './layer';

export type ThreeContext = {
  THREE: typeof THREE;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  /** Ambient + key + rim lights; key casts soft shadows. Returns the key light. */
  studioLights: (opts?: { intensity?: number; keyPosition?: [number, number, number]; color?: number }) => THREE.DirectionalLight;
  /** Image-based lighting for reflections on metal / glossy / glass materials. */
  environment: (intensity?: number) => void;
  /** Transparent ground that only shows the contact shadow. */
  groundShadow: (opts?: { y?: number; opacity?: number; size?: number }) => THREE.Mesh;
  roundedBox: (w: number, h: number, d: number, r: number, segments?: number) => RoundedBoxGeometry;
};

/**
 * Render a Three.js scene to a transparent bitmap placed at (x, y, w, h). The bitmap is
 * w*scale*supersample pixels wide, so it stays sharp in the scaled PNG.
 */
export function ThreeLayer({ id, x, y, w, h, fov = 30, cameraPosition = [4, 3, 6], lookAt = [0, 0, 0], supersample = 1, build }: {
  id: string; x: number; y: number; w: number; h: number; fov?: number; cameraPosition?: [number, number, number]; lookAt?: [number, number, number];
  supersample?: number; build: (ctx: ThreeContext) => void;
}) {
  const href = useMemo(() => {
    const k = renderScale() * supersample, pw = Math.ceil(w * k), ph = Math.ceil(h * k);
    const canvas = document.createElement('canvas');
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true, premultipliedAlpha: false });
    try {
      renderer.setPixelRatio(1);
      renderer.setSize(pw, ph, false);
      renderer.setClearColor(0x000000, 0);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(fov, w / h, 0.1, 200);
      camera.position.set(...cameraPosition);
      camera.lookAt(...lookAt);
      const ctx: ThreeContext = {
        THREE, scene, camera, renderer,
        studioLights: ({ intensity = 1, keyPosition = [4, 7, 5], color = 0xffffff } = {}) => {
          scene.add(new THREE.HemisphereLight(0xffffff, 0x8892a6, 0.9 * intensity));
          const key = new THREE.DirectionalLight(color, 2.2 * intensity);
          key.position.set(...keyPosition);
          key.castShadow = true;
          key.shadow.mapSize.set(2048, 2048);
          key.shadow.radius = 6;
          Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 0.5, far: 40 });
          key.shadow.bias = -0.0005;
          scene.add(key);
          const rim = new THREE.DirectionalLight(0xffffff, 0.8 * intensity);
          rim.position.set(-5, 3, -4);
          scene.add(rim);
          return key;
        },
        environment: (intensity = 1) => {
          const pm = new THREE.PMREMGenerator(renderer);
          scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
          scene.environmentIntensity = intensity;
          pm.dispose();
        },
        groundShadow: ({ y: gy = 0, opacity = 0.25, size = 20 } = {}) => {
          const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.ShadowMaterial({ opacity }));
          m.rotation.x = -Math.PI / 2;
          m.position.y = gy;
          m.receiveShadow = true;
          scene.add(m);
          return m;
        },
        roundedBox: (bw, bh, bd, r, segments = 6) => new RoundedBoxGeometry(bw, bh, bd, segments, r),
      };
      build(ctx);
      renderer.render(scene, camera);
      return canvas.toDataURL('image/png');
    } finally {
      renderer.dispose();
      renderer.forceContextLoss();
    }
  }, []);
  return <image id={id} data-render="three" data-raster="three" x={x} y={y} width={w} height={h} href={href} preserveAspectRatio="xMidYMid meet" />;
}
