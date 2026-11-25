"""Create clearly labelled, editable SVG visual fallbacks; never imitate trademarks."""
import hashlib
import html
from pathlib import Path

def create(destination,label,parent_path=None,parent_name=None):
    """Write a transparent product tile, with an associated mark when verified."""
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    text=html.escape(label);parent=html.escape(parent_name or '')
    color='#'+hashlib.sha256((parent_name or label).encode()).hexdigest()[:6]
    initials=''.join(word[0] for word in label.split() if word)[:2].upper() or '+'
    visual=f'<rect x="4" y="4" width="56" height="56" rx="16" fill="{color}"/><path d="M16 48L48 16" stroke="white" stroke-opacity=".28" stroke-width="3"/><text x="32" y="39" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="white">{html.escape(initials)}</text>'
    type='generated_associated_product_badge' if parent_path else 'generated_visual_fallback'
    destination.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{text} — {parent} product fallback">{visual}</svg>',encoding='utf-8')
    return {'path':str(destination),'representation_type':type,'parent_name':parent_name}
