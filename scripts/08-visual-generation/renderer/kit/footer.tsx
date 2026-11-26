import React from 'react';
import defaultFooter from '../../../../references/assets/t01-footer.png';

/** Omitted fields retain the original T01 artwork. A null badge removes it. */
export type FooterContent = {
  name?: string;
  portraitHref?: string;
  brandHref?: string;
  brandLabel?: string;
  badgeHref?: string | null;
};

export type FooterProps = {
  width: number;
  y: number;
  x?: number;
  id?: string;
  content?: FooterContent;
};

/** Natural height for a footer spanning the given width. */
export function footerHeight(width: number): number { return width * 117 / 1398; }

/** The default is the exact T01 strip; individual overrides use editable SVG text. */
export function Footer({width, y, x=0, id='footer', content}: FooterProps) {
  const scale=width/1398;
  if (!content) return <image id={id} x={x} y={y} width={width} height={footerHeight(width)} href={defaultFooter} preserveAspectRatio="xMidYMid meet" />;
  const clipId=`${id}-portrait-clip`;
  return <g id={id} transform={`translate(${x} ${y}) scale(${scale})`}>
    <image href={defaultFooter} width="1398" height="117" />
    {content.portraitHref !== undefined && <>
      <defs><clipPath id={clipId}><circle cx="92" cy="62" r="30" /></clipPath></defs>
      <rect x="58" y="27" width="67" height="70" fill="white" />
      <image href={content.portraitHref} x="62" y="32" width="60" height="60" preserveAspectRatio="xMidYMid slice" clipPath={`url(#${clipId})`} />
      <circle cx="92" cy="62" r="30" fill="none" stroke="#111" strokeWidth="2" />
    </>}
    {content.name !== undefined && <>
      <rect x="132" y="35" width="230" height="50" fill="white" />
      <text x="139" y="68" fontFamily="Arial, sans-serif" fontWeight="700" fontSize="25" {...(content.name.length>17 ? {textLength:220,lengthAdjust:'spacingAndGlyphs'} : {})}>{content.name}</text>
    </>}
    {content.badgeHref !== undefined && <>
      <rect x="365" y="42" width="32" height="38" fill="white" />
      {content.badgeHref && <image href={content.badgeHref} x="368" y="47" width="25" height="25" preserveAspectRatio="xMidYMid meet" />}
    </>}
    {content.brandHref !== undefined && <>
      <rect x="1163" y="32" width="57" height="60" fill="white" />
      <image href={content.brandHref} x="1168" y="41" width="46" height="45" preserveAspectRatio="xMidYMid meet" />
    </>}
    {content.brandLabel !== undefined && <>
      <rect x="1220" y="35" width="171" height="52" fill="white" />
      <text x="1225" y="72" fontFamily="Arial, sans-serif" fontWeight="600" fontSize="30" {...(content.brandLabel.length>10 ? {textLength:160,lengthAdjust:'spacingAndGlyphs'} : {})}>{content.brandLabel}</text>
    </>}
  </g>;
}
