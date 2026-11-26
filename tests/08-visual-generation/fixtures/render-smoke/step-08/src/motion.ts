export function buildTimeline(svg: SVGSVGElement, gsap: typeof import('gsap').gsap) {
  const tl = gsap.timeline();
  tl.from(svg.querySelector('#node-1'), { opacity: 0, y: 12, duration: 0.4 })
    .from(svg.querySelector('#conn-1'), { strokeDasharray: 80, strokeDashoffset: 80, duration: 0.4 })
    .from(svg.querySelector('#node-2'), { opacity: 0, y: 12, duration: 0.4 });
  return tl;
}
