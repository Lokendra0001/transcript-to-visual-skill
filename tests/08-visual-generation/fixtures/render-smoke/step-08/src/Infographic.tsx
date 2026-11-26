import { wrapText } from '@kit';
import mark from '../../assets/mark.png';

const FONT = '700 20px -apple-system, Helvetica, Arial, sans-serif';
const steps = ['Attract the right audience', 'Capture and nurture leads'];

export default function Infographic() {
  return (
    <svg id="infographic" xmlns="http://www.w3.org/2000/svg" width={640} height={260} viewBox="0 0 640 260">
      <rect id="bg" width={640} height={260} fill="#F8F4F0" />
      {steps.map((s, i) => {
        const x = 40 + i * 320, lines = wrapText(s, FONT, 200);
        return (
          <g key={s} id={`node-${i + 1}`} data-node={`node-${i + 1}`}>
            <rect id={`node-${i + 1}-box`} x={x} y={60} width={240} height={140} rx={16} fill="#fff" stroke="#1F1F1F" strokeWidth={3} />
            <image id={`node-${i + 1}-logo`} data-asset={`ar-${i + 1}`} href={mark} x={x + 20} y={80} width={32} height={32} />
            <text id={`node-${i + 1}-label`} data-fit={`node-${i + 1}-box`} x={x + 20} y={140} style={{ font: FONT }} fill="#1F1F1F">
              {lines.map((l, j) => <tspan key={j} x={x + 20} dy={j ? 24 : 0}>{l}</tspan>)}
            </text>
          </g>
        );
      })}
      <path id="conn-1" data-connection="conn-1" d="M280 130 H360" stroke="#1F1F1F" strokeWidth={3} fill="none" />
    </svg>
  );
}
