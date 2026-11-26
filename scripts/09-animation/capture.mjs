#!/usr/bin/env node
// Capture the existing Step 08 GSAP page at exact timeline timestamps.
import { chromium } from '../08-visual-generation/renderer/node_modules/playwright-core/index.mjs';
import { mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [pageFile, framesDir, widthArg, heightArg, fpsArg, durationArg, holdArg, chrome] = process.argv.slice(2);
const width=Number(widthArg), height=Number(heightArg), fps=Number(fpsArg), duration=Number(durationArg), hold=Number(holdArg);
if (!pageFile || !framesDir || !chrome || ![width,height,fps,duration,hold].every(Number.isFinite) || width<=0 || height<=0 || fps<=0 || duration<=0 || hold<0) throw new Error('invalid capture arguments');
await mkdir(framesDir, { recursive: true });
const browser=await chromium.launch({executablePath:chrome,headless:true,args:['--disable-gpu','--host-resolver-rules=MAP * ~NOTFOUND','--enable-unsafe-swiftshader']});
try {
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  await page.route('**/*', route => { const u=route.request().url(); return (u.startsWith('file:') || u.startsWith('data:')) ? route.continue() : route.abort(); });
  const count=Math.ceil((duration+hold)*fps);
  for(let i=0;i<count;i++) {
    const time=Math.min(i/fps,duration);
    await page.goto(pathToFileURL(resolve(pageFile)).href+'#t='+time,{waitUntil:'load'});
    if(i>0) await page.reload({waitUntil:'load'});
    await page.waitForFunction(() => document.title==='seeked',null,{timeout:30000});
    const svg=page.locator('svg#infographic');
    await svg.screenshot({path:join(framesDir,`frame-${String(i).padStart(5,'0')}.png`),animations:'allow'});
  }
  console.log(JSON.stringify({frames:count,fps,duration,hold}));
} finally { await browser.close(); }
