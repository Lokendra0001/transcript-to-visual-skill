#!/usr/bin/env node
// Step 08 renderer: bundles <run>/step-08/src (React + SVG, optional GSAP motion layer),
// renders it in headless Chrome, serializes the live SVG, captures a PNG of that SVG file,
// and writes a render report with in-browser layout checks. It never designs anything.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import * as esbuild from 'esbuild';

const HERE = dirname(fileURLToPath(import.meta.url));
const MAC_CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');
const version = (pkg) => JSON.parse(readFileSync(join(HERE, 'node_modules', pkg, 'package.json'), 'utf8')).version;

const { values: args } = parseArgs({ options: {
  'run-dir': { type: 'string' }, scale: { type: 'string', default: '2' },
  chrome: { type: 'string', default: process.env.CHROME_PATH || MAC_CHROME },
} });
if (!args['run-dir']) { console.error('usage: render.mjs --run-dir <run-dir> [--scale 2] [--chrome <path>]'); process.exit(64); }
const runDir = resolve(args['run-dir']);
const stepDir = join(runDir, 'step-08');
const srcDir = join(stepDir, 'src');
const buildDir = join(stepDir, 'build');
const entry = join(srcDir, 'Infographic.tsx');
const motionEntry = join(srcDir, 'motion.ts');
const scale = Number(args.scale);
if (!existsSync(entry)) { console.error(`missing ${entry}`); process.exit(64); }
if (!existsSync(args.chrome)) { console.error(`Chrome not found at ${args.chrome}; pass --chrome or CHROME_PATH`); process.exit(64); }
mkdirSync(buildDir, { recursive: true });

// ---- in-page code -------------------------------------------------------
const PAGE_COMMON = `
globalThis.__kitScale = ${scale};
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import Infographic from ${JSON.stringify(entry)};
const tick = (ms = 0) => new Promise((r) => setTimeout(r, ms));
const out = (data) => {
  const pre = document.createElement('pre'); pre.id = 'out';
  pre.textContent = btoa(unescape(encodeURIComponent(JSON.stringify(data))));
  document.body.appendChild(pre);
};
async function mount() {
  await document.fonts.ready;
  const host = document.getElementById('root');
  flushSync(() => createRoot(host).render(<Infographic />));
  const svg = host.querySelector('svg#infographic');
  if (!svg) throw new Error('component must render a root <svg id="infographic">');
  // Async kit layers (e.g. AntV) register their work; wait for it, including work queued by work.
  for (let round = 0; round < 10 && globalThis.__kitPending?.length; round++) {
    const work = globalThis.__kitPending; globalThis.__kitPending = [];
    await Promise.all(work);
  }
  await Promise.all([...svg.querySelectorAll('image')].map((im) => new Promise((ok) => {
    const href = im.getAttribute('href') || im.getAttribute('xlink:href') || '';
    const probe = new Image(); probe.onload = probe.onerror = () => ok(); probe.src = href; setTimeout(ok, 3000);
  })));
  await document.fonts.ready;
  await tick(50);
  return svg;
}
`;

const APP_PAGE = PAGE_COMMON + `
const inside = (a, b, tol = 0.5) => a.left >= b.left - tol && a.top >= b.top - tol && a.right <= b.right + tol && a.bottom <= b.bottom + tol;
const box = (r) => ({ x: +r.left.toFixed(1), y: +r.top.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) });
(async () => {
  const errors = [], warnings = [];
  try {
    const svg = await mount();
    const canvas = svg.getBoundingClientRect();
    for (const a of ['width', 'height', 'viewBox']) if (!svg.getAttribute(a)) errors.push('root svg missing ' + a);
    const ids = [...svg.querySelectorAll('[id]')].map((e) => e.id);
    const dup = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
    if (dup.length) errors.push('duplicate ids: ' + dup.join(', '));
    if (svg.querySelector('foreignObject')) errors.push('foreignObject is not allowed');
    if (svg.querySelector('script')) errors.push('script elements are not allowed');
    for (const im of svg.querySelectorAll('image')) {
      const href = im.getAttribute('href') || im.getAttribute('xlink:href') || '';
      if (!href.startsWith('data:')) errors.push('non-embedded image href on ' + (im.id || im.closest('[id]')?.id || '<image>'));
      if (im.getAttribute('preserveAspectRatio') === 'none') errors.push('distorted image (preserveAspectRatio=none) on ' + (im.id || '<image>'));
    }
    // References: every url(#…) and href="#…" must resolve inside the SVG (filters, gradients, clips, markers).
    const local = new Set(ids);
    for (const el of svg.querySelectorAll('*')) for (const a of el.attributes) {
      for (const m of a.value.matchAll(/url\\(\\s*['"]?#([^'")\\s]+)/g)) if (!local.has(m[1])) errors.push('unresolved reference url(#' + m[1] + ') on ' + (el.id || el.tagName));
      if ((a.name === 'href' || a.name === 'xlink:href') && a.value.startsWith('#') && !local.has(a.value.slice(1))) errors.push('unresolved reference ' + a.value + ' on ' + (el.id || el.tagName));
    }
    // Brand logos: no effect may alter their pixels or proportions.
    const outerOnly = (f) => {
      const kids = [...f.children];
      if (kids.length && kids.every((k) => k.tagName === 'feDropShadow')) return true;
      const merge = kids[kids.length - 1];
      return merge?.tagName === 'feMerge' && merge.lastElementChild?.getAttribute('in') === 'SourceGraphic';
    };
    for (const im of svg.querySelectorAll('image[data-asset]')) {
      const who = im.getAttribute('data-asset');
      for (const a of ['filter', 'mask']) if (im.getAttribute(a) || getComputedStyle(im)[a] !== 'none') errors.push('brand logo has its own ' + a + ': ' + who);
      if (+getComputedStyle(im).opacity < 1) errors.push('brand logo is semi-transparent: ' + who);
      for (let e = im.parentElement; e && e !== svg.parentElement; e = e.parentElement) {
        const ref = (e.getAttribute('filter') || '').match(/url\\(#([^)]+)\\)/);
        const f = ref && svg.querySelector('#' + CSS.escape(ref[1]));
        if (f && !outerOnly(f)) errors.push('filter #' + ref[1] + ' on ' + (e.id || e.tagName) + ' alters brand logo ' + who + ' (only outer shadow/glow filters may wrap logos)');
        if (e.getAttribute('mask')) errors.push('mask on ' + (e.id || e.tagName) + ' covers brand logo ' + who);
      }
      const m = im.getCTM();
      if (m && (Math.abs(m.b) > 1e-3 || Math.abs(m.c) > 1e-3 || Math.abs(Math.abs(m.a) - Math.abs(m.d)) > 1e-3)) errors.push('brand logo is skewed, rotated or non-uniformly scaled: ' + who);
    }
    // Every embedded bitmap, with its pixel density; kit rasters (Three.js) must be at least the capture scale.
    const images = await Promise.all([...svg.querySelectorAll('image')].map((im) => new Promise((ok) => {
      const probe = new Image();
      probe.onload = probe.onerror = () => {
        const r = im.getBoundingClientRect(), kind = im.hasAttribute('data-asset') ? 'asset' : im.getAttribute('data-raster') ? 'raster' : 'other';
        const density = r.width ? +(Math.min(probe.naturalWidth / r.width, probe.naturalHeight / r.height)).toFixed(2) : 0;
        ok({ element_id: im.id || null, kind, technology: im.getAttribute('data-raster') || null, natural: [probe.naturalWidth, probe.naturalHeight], bounds: box(r), density });
      };
      probe.src = im.getAttribute('href') || im.getAttribute('xlink:href') || '';
    })));
    for (const i of images) if (i.kind === 'raster' && i.density < ${scale} * 0.98) errors.push('raster ' + i.element_id + ' is ' + i.density + 'x, below the ${scale}x capture scale');
    const layers = [...svg.querySelectorAll('[data-render]')].map((e) => ({ element_id: e.id || null, technology: e.getAttribute('data-render'), bounds: box(e.getBoundingClientRect()) }));
    for (const l of layers) if (!inside(l.bounds && { left: l.bounds.x, top: l.bounds.y, right: l.bounds.x + l.bounds.w, bottom: l.bounds.y + l.bounds.h }, canvas)) warnings.push('render layer extends outside canvas: ' + l.element_id);
    const count = (sel) => svg.querySelectorAll(sel).length;
    const effects = { filters: count('filter'), linear_gradients: count('linearGradient'), radial_gradients: count('radialGradient'), patterns: count('pattern'), clip_paths: count('clipPath'), masks: count('mask'), markers: count('marker') };
    const fit = [];
    for (const el of svg.querySelectorAll('[data-fit]')) {
      const c = svg.getElementById(el.dataset.fit) || svg.querySelector('#' + CSS.escape(el.dataset.fit));
      if (!c) { errors.push('data-fit container not found: ' + el.dataset.fit); continue; }
      const t = el.getBoundingClientRect(), k = c.getBoundingClientRect();
      const ok = inside(t, k);
      fit.push({ element: el.id || null, container: el.dataset.fit, ok, text: box(t), box: box(k) });
      if (!ok) errors.push('text overflows its box: ' + (el.id || el.textContent.slice(0, 40)) + ' in ' + el.dataset.fit);
    }
    const collect = (attr) => [...svg.querySelectorAll('[' + attr + ']')].map((e) => {
      const r = e.getBoundingClientRect();
      if (!inside(r, canvas)) errors.push(attr + ' outside canvas: ' + e.getAttribute(attr));
      if (r.width === 0 && r.height === 0) warnings.push(attr + ' has empty bounds: ' + e.getAttribute(attr));
      return { id: e.getAttribute(attr), element_id: e.id || null, bounds: box(r) };
    });
    const nodes = collect('data-node'), connections = collect('data-connection'), assets = collect('data-asset');
    const fonts = [...new Set([...svg.querySelectorAll('text')].map((t) => getComputedStyle(t).fontFamily))];
    const svgText = new XMLSerializer().serializeToString(svg);
    out({ ok: true, errors, warnings, width: +svg.getAttribute('width'), height: +svg.getAttribute('height'),
      nodes, connections, assets, text_fit: fit, fonts, render_layers: layers, images, effects, svg: svgText });
  } catch (e) { out({ ok: false, errors: [String(e && e.stack || e)], warnings }); }
})();
`;

const MOTION_PAGE = PAGE_COMMON + `
import { gsap } from 'gsap';
import { buildTimeline } from ${JSON.stringify(motionEntry)};
const state = (svg) => Object.fromEntries([...svg.querySelectorAll('[id]')].map((e) => {
  const r = e.getBoundingClientRect(), s = getComputedStyle(e);
  return [e.id, [r.left, r.top, r.width, r.height, +s.opacity, s.visibility, s.strokeDashoffset]];
}));
(async () => {
  const errors = [];
  try {
    const svg = await mount();
    const before = state(svg);
    const tl = buildTimeline(svg, gsap);
    if (!tl || typeof tl.progress !== 'function') throw new Error('buildTimeline(svg, gsap) must return a gsap timeline');
    tl.pause();
    const targets = [...new Set(tl.getChildren(true, true, false).flatMap((t) => t.targets()).map((n) => n.id || '<no id>'))];
    if (targets.includes('<no id>')) errors.push('timeline animates an element without an id');
    const mode = location.hash.slice(1);
    if (mode === 'check') {
      tl.progress(1);
      await tick(0);
      const after = state(svg), diffs = [];
      for (const [id, a] of Object.entries(before)) {
        const b = after[id];
        if (!b) { diffs.push(id + ' removed'); continue; }
        const moved = a.slice(0, 4).some((v, i) => Math.abs(v - b[i]) > 0.5);
        if (moved || Math.abs(a[4] - b[4]) > 0.01 || a[5] !== b[5] || a[6] !== b[6]) diffs.push(id);
      }
      if (diffs.length) errors.push('final frame differs from static master: ' + diffs.slice(0, 20).join(', '));
      out({ ok: true, errors, duration: tl.duration(), targets, final_frame_matches_static: diffs.length === 0 });
    } else if (mode.startsWith('t=')) {
      tl.seek(Math.min(+mode.slice(2), tl.duration()));
      document.title = 'seeked';
    } else {
      window.__timeline = tl; tl.play(0);
    }
  } catch (e) { out({ ok: false, errors: [String(e && e.stack || e)] }); }
})();
`;

const HTML = (body, css = '') => `<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#fff}svg{display:block}${css}</style></head><body>${body}</body></html>`;

async function bundle(code, name) {
  const result = await esbuild.build({
    stdin: { contents: code, loader: 'tsx', resolveDir: srcDir, sourcefile: `${name}.tsx` },
    bundle: true, write: false, format: 'iife', platform: 'browser', target: 'chrome120',
    jsx: 'automatic', outdir: buildDir, nodePaths: [join(HERE, 'node_modules')],
    alias: { '@kit': join(HERE, 'kit') }, absWorkingDir: runDir, logLevel: 'silent',
    loader: { '.png': 'dataurl', '.jpg': 'dataurl', '.jpeg': 'dataurl', '.webp': 'dataurl', '.svg': 'dataurl',
              '.woff2': 'dataurl', '.woff': 'dataurl', '.ttf': 'dataurl', '.otf': 'dataurl' },
    define: { 'process.env.NODE_ENV': '"production"' }, minify: true,
  });
  const js = result.outputFiles.find((f) => f.path.endsWith('.js')).text;
  const css = result.outputFiles.find((f) => f.path.endsWith('.css'))?.text || '';
  const file = join(buildDir, `${name}.html`);
  writeFileSync(file, HTML(`<div id="root"></div><script>${js.replaceAll('</script', '<\\/script')}</script>`, css));
  return file;
}

// WebGL through SwiftShader (Three.js layers) and no network at all: every input is local and embedded.
const CHROME_FLAGS = ['--enable-unsafe-swiftshader', '--host-resolver-rules=MAP * ~NOTFOUND'];

function chrome(extra, url) {
  const profile = mkdtempSync(join(tmpdir(), 'ttv-chrome-'));
  try {
    return execFileSync(args.chrome, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
      '--hide-scrollbars', `--user-data-dir=${profile}`, ...CHROME_FLAGS, ...extra, url],
      { encoding: 'utf8', maxBuffer: 512 * 1024 * 1024, timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
  } finally { rmSync(profile, { recursive: true, force: true }); }
}

function readOut(dom) {
  const m = dom.match(/<pre id="out">([^<]*)<\/pre>/);
  if (!m) throw new Error('page did not finish (no #out); check the component for runtime errors or long work');
  return JSON.parse(Buffer.from(m[1], 'base64').toString('utf8'));
}

function pngSize(file) {
  const b = readFileSync(file);
  if (b.length < 24 || b.toString('latin1', 1, 4) !== 'PNG') throw new Error('invalid PNG');
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}

function hashTree(dir) {
  const out = {};
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) Object.assign(out, hashTree(p));
    else out[relative(runDir, p)] = sha256(readFileSync(p));
  }
  return out;
}

// ---- run ------------------------------------------------------------------
const report = { step: '08-visual-generation', tool: 'scripts/08-visual-generation/renderer/render.mjs',
  timestamp: new Date().toISOString(), status: 'failed', errors: [], warnings: [],
  versions: { node: process.version, ...Object.fromEntries(['react', 'react-dom', 'gsap', 'esbuild', '@svgdotjs/svg.js', 'zdog', 'three', '@antv/infographic'].map((p) => [p, version(p)])) },
  environment: { chrome_flags: CHROME_FLAGS, network: 'blocked (host resolver maps every host to NOTFOUND)' },
  inputs: hashTree(srcDir), outputs: {} };
try {
  report.versions.chrome = execFileSync(args.chrome, ['--version'], { encoding: 'utf8' }).trim();
  const appHtml = await bundle(APP_PAGE, 'app');
  const page = readOut(chrome(['--virtual-time-budget=15000', '--dump-dom'], pathToFileURL(appHtml).href));
  report.errors.push(...page.errors); report.warnings.push(...(page.warnings || []));
  if (page.ok) {
    const { svg, ...rest } = page;
    const svgFile = join(stepDir, 'infographic.svg');
    writeFileSync(svgFile, `<?xml version="1.0" encoding="UTF-8"?>\n${svg}\n`);
    Object.assign(report, { width: rest.width, height: rest.height, nodes: rest.nodes, connections: rest.connections,
      assets: rest.assets, text_fit: rest.text_fit, fonts: rest.fonts, render_layers: rest.render_layers, images: rest.images, effects: rest.effects });
    // Capture the serialized SVG file itself, so the PNG shows exactly what was delivered.
    const snapshot = join(buildDir, 'snapshot.html');
    writeFileSync(snapshot, HTML(svg));
    const pngFile = join(stepDir, 'infographic.png');
    rmSync(pngFile, { force: true });
    chrome([`--window-size=${rest.width},${rest.height}`, `--force-device-scale-factor=${scale}`, '--virtual-time-budget=5000',
      `--screenshot=${pngFile}`], pathToFileURL(snapshot).href);
    const dims = pngSize(pngFile);
    const want = [Math.round(rest.width * scale), Math.round(rest.height * scale)];
    if (dims[0] !== want[0] || dims[1] !== want[1]) report.errors.push(`PNG is ${dims.join('x')}, expected ${want.join('x')}`);
    report.outputs = { svg: { path: relative(runDir, svgFile), sha256: sha256(readFileSync(svgFile)) },
      png: { path: relative(runDir, pngFile), sha256: sha256(readFileSync(pngFile)), dimensions: dims, scale } };
  }
  if (existsSync(motionEntry)) {
    const motionHtml = await bundle(MOTION_PAGE, 'motion');
    const m = readOut(chrome(['--virtual-time-budget=15000', '--dump-dom'], pathToFileURL(motionHtml).href + '#check'));
    report.motion = { page: relative(runDir, motionHtml), ...m };
    report.errors.push(...m.errors.map((e) => 'motion: ' + e));
  }
} catch (e) { report.errors.push(String(e && e.message || e)); }
report.status = report.errors.length ? 'failed' : 'rendered';
writeFileSync(join(stepDir, 'render-report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ status: report.status, errors: report.errors, warnings: report.warnings, outputs: report.outputs, motion: report.motion && { duration: report.motion.duration, final_frame_matches_static: report.motion.final_frame_matches_static } }, null, 2));
process.exit(report.errors.length ? 2 : 0);
