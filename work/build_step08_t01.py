#!/usr/bin/env python3
"""Direct SVG composition for the selected T01 modular GTM template."""
import base64, html, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; RUN=ROOT/'runs/2026-11-24-abm-playbook-chat'; OUT=RUN/'step-08'
sys.path.insert(0,str(ROOT/'scripts/08-visual-generation'))
from embed_assets import embed_asset

W,H=1400,2440
def esc(v): return html.escape(str(v),quote=True)
def main():
 a=json.loads((RUN/'04-workflow-architecture.json').read_text()); c=json.loads((RUN/'05-content-writing.json').read_text()); r=json.loads((RUN/'07-logo-retrieval.json').read_text())
 copy={t:x['preferred_text'] for x in c['content_items'] if x.get('preferred_text') for t in x.get('target_refs',[])}
 assets={x['id']:x for x in r['assets']+r['fallback_assets']}; usage={x['target_id']:assets[x['asset_id']] for x in r['asset_mappings']}
 uris={}
 for target,asset in usage.items():
  p=RUN/asset['prepared_file_path']; z=embed_asset(p,RUN)
  if z.get('data_uri'): uris[target]=z['data_uri']
 parts=[]
 def add(s): parts.append(s)
 def rect(id,x,y,w,h,fill='#fff',stroke='#242424',rx=18,sw=2): add(f'<rect id="{esc(id)}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
 def text(id,x,y,s,size=18,weight=500,fill='#202124',anchor='start'): add(f'<text id="{esc(id)}" x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')
 def path(id,d,stroke='#242424',dash='',op=1,marker=''): add(f'<path id="{esc(id)}" d="{d}" fill="none" stroke="{stroke}" stroke-width="2" opacity="{op}" {"stroke-dasharray=\""+dash+"\"" if dash else ""} {"marker-end=\"url(#arrow)\"" if marker else ""}/>')
 def tab(num,title,x,y,w,accent='#3fe4aa'):
  add(f'<g id="node-step-{num}"><path d="M{x} {y+46} L{x} {y} H{x+min(w,420)} L{x+min(w,450)} {y+46} Z" fill="#f8f5f1" stroke="#242424" stroke-width="2"/>')
  rect(f'step-{num}-badge',x,y,62,46,accent,'#242424',0,2); text(f'step-{num}-number',x+31,y+31,f'{num:02d}',23,800,'#202124','middle'); text(f'step-{num}-header',x+78,y+31,title,23,800)
 def tile(nid,x,y,w=134,h=64):
  rect(nid,x,y,w,h,'#fff','#242424',12,1.5)
  if nid in uris: add(f'<image id="{nid}-logo" href="{uris[nid]}" x="{x+10}" y="{y+11}" width="36" height="36" preserveAspectRatio="xMidYMid meet"/>')
  else: rect(f'{nid}-fallback',x+10,y+14,30,30,'#eee7ff','#7c4ddf',8,1)
  label=copy.get(nid,nid); text(f'{nid}-label',x+52,y+38,label,13,700)
 def miniasset(nid,x,y):
  rect(nid,x,y,34,34,'#fff','#242424',7,1)
  if nid in uris: add(f'<image id="{nid}-logo" href="{uris[nid]}" x="{x+5}" y="{y+5}" width="24" height="24" preserveAspectRatio="xMidYMid meet"/>')
  text(f'{nid}-label',x+40,y+22,copy[nid],10,700)
 def chip(nid,x,y,w,h=31,fill='#fff'):
  rect(nid,x,y,w,h,fill,'#242424',8,1); add(f'<circle id="{nid}-dot" cx="{x+14}" cy="{y+15}" r="5" fill="#3fe4aa"/>'); text(f'{nid}-label',x+27,y+21,copy[nid],12,600)
 # Canvas, reference-derived title band and dotted field.
 add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.5" fill="#dfd3cb"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#242424"/></marker><filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity=".13"/></filter></defs>')
 rect('background',0,0,W,H,'#faf6f1','none',0,0); rect('dot-field',28,205,W-56,H-235,'url(#dots)','#b8aaa1',28,3)
 add('<path id="top-arch-left" d="M0 74 H160 Q180 74 184 100 L190 122 H0Z" fill="#d8c7bf"/><path id="top-arch-right" d="M1210 75 H1400 V150 H1190 L1202 96 Q1206 75 1210 75Z" fill="#c9b4ac"/>')
 text('node-title',76,116,copy['node-title'],52,900); text('visual-unit-001',780,110,copy['visual-unit-001'],13,700)
 add('<rect id="title-band" x="54" y="130" width="1292" height="112" rx="16" fill="#7c4ddf" filter="url(#shadow)"/>'); text('title-band-text',78,211,'ABM PLAYBOOK',76,900,'#fff')
 text('node-optionality-note',75,274,copy['node-optionality-note'],14,600,'#242424')
 # Step 1
 rect('step-1-card',55,302,1290,285,'#fff','#242424',22,2); tab(1,copy['node-step-1'],55,302,1290)
 rect('node-step-1-card',88,378,350,147,'#f8f5f1','#242424',14,1.5); text('node-step-1-title',112,414,'Identify accounts and stakeholders',17,800); text('node-step-1-subtitle',112,445,'Define your TAM, then map stakeholders',13,500)
 rect('node-step-1-start',82,471,105,46,'#3fe4aa','#242424',14,2); text('node-step-1-start-label',136,501,'Start',17,800,'#202124','middle'); path('connection-001-label-path','M187 494 H240 V426 H278',marker='yes')
 text('step-1-tools-label',502,374,'Tools (optional alternatives)',17,800)
 for i,n in enumerate([f'node-s1-tool-{x:02d}' for x in range(1,9)]): tile(n,500+(i%4)*202,395+(i//4)*78,182,60)
 # step 2 / step 3
 rect('step-2-card',55,625,600,300,'#fff','#242424',22,2); tab(2,copy['node-step-2'],55,625,600,'#8453df')
 for i,n in enumerate([f'node-s2-tool-{x:02d}' for x in range(1,11)]): tile(n,82+(i%4)*135,700+(i//4)*70,125,58)
 rect('step-3-card',700,625,645,300,'#fff','#242424',22,2); tab(3,copy['node-step-3'],700,625,645)
 groups=[('node-s3-group-034',range(47,55),'#e8f0ff'),('node-s3-group-035',range(55,61),'#e9fbf0'),('node-s3-group-033',range(36,47),'#f8edff')]
 for gi,(g,nums,fill) in enumerate(groups):
  y=[695,767,839][gi]; h=[61,61,82][gi]; rect(g,730,y,585,h,fill,'#242424',12,1); text(g+'-label',754,y+25,copy[g],16,800)
  ns=[f'node-s3-sig-{i:03d}' for i in nums]; x=950
  cols=4 if gi==2 else 3; gap=90 if gi==2 else 118
  for j,n in enumerate(ns): text(n,x+(j%cols)*gap,y+24+(j//cols)*18,copy[n],9 if gi==2 else 11,600); add(f'<rect id="{n}-check" x="{x-15+(j%cols)*gap}" y="{y+14+(j//cols)*18}" width="9" height="9" rx="2" fill="#3fe4aa"/>')
 text('section-step-3-label',730,914,copy['section-step-3'],12,600,'#4a4a4a')
 # Step 4 / 5
 rect('step-4-card',55,966,610,355,'#fff','#242424',22,2); tab(4,copy['node-step-4'],55,966,610)
 rect('node-s4-model-awareness',82,1040,270,235,'#f8f5f1','#242424',12,1); text('node-s4-model-awareness-label',100,1070,copy['node-s4-model-awareness'],16,800)
 for i,n in enumerate([f'node-s4-stage-{x}' for x in range(1,6)]): chip(n,100,1084+i*35,232,29,['#d9faec','#c8f5ed','#c4e7ff','#dfd2ff','#cdb2fa'][i])
 rect('node-s4-model-tiers',374,1040,260,235,'#f8f5f1','#242424',12,1); text('node-s4-model-tiers-label',392,1070,copy['node-s4-model-tiers'],16,800)
 for i,n in enumerate([f'node-s4-tier-{x}' for x in range(1,4)]): chip(n,394,1093+i*51,218,38,'#292929' if i==0 else '#fff')
 text('connection-031-label',82,1306,copy['connection-031'],12,600,'#4a4a4a'); tile('node-s4-tool-01',548,986,86,43)
 rect('step-5-card',700,966,645,355,'#fff','#242424',22,2); tab(5,copy['node-step-5'],700,966,645,'#8453df')
 tile('node-s5-tool-01',742,1050,210,73); text('crm-or',849,1148,'OR',14,800,'#242424','middle'); tile('node-s5-tool-02',742,1165,210,73)
 rect('node-s5-crm-records',1000,1050,305,190,'#f8f5f1','#242424',12,1); text('node-s5-crm-records-label',1020,1080,copy['node-s5-crm-records'],18,800)
 for i,s in enumerate(['Account and stakeholder context','Signals and engagement history','Prioritization and next steps']): text(f'crm-record-{i}',1045,1120+i*32,s,13,600); add(f'<rect id="crm-record-{i}-check" x="1022" y="{1108+i*32}" width="13" height="13" rx="3" fill="#3fe4aa"/>')
 path('connection-010-label-path','M952 1087 H1000',marker='yes'); text('connection-010-label',820,1027,copy['connection-010'],12,600); text('connection-033-label',742,1268,copy['connection-033'],12,600)
 # Step 6
 rect('step-6-card',55,1360,1290,510,'#fff','#242424',22,2); tab(6,copy['node-step-6'],55,1360,1290,'#8453df')
 rect('node-s6-lane-one-to-one',85,1440,580,365,'#f0fff6','#242424',16,1.5); text('node-s6-lane-one-to-one-label',110,1475,copy['node-s6-lane-one-to-one'],22,800)
 one=['node-s6-007','node-s6-008','node-s6-009','node-s6-010'];
 for i,n in enumerate(one): chip(n,110,1500+i*65,350,42,'#fff'); tool={'node-s6-007':'node-s6-007-tool-01','node-s6-010':'node-s6-010-tool-01'}.get(n); (tile(tool,475,1491+i*65,160,55) if tool else None)
 rect('node-s6-lane-one-to-many',735,1440,580,365,'#fcf0ff','#242424',16,1.5); text('node-s6-lane-one-to-many-label',760,1475,copy['node-s6-lane-one-to-many'],22,800)
 many=['node-s6-011','node-s6-012','node-s6-013','node-s6-014','node-s6-015','node-s6-016','node-s6-017','node-s6-018']; toolmap={'node-s6-013':['node-s6-013-tool-01','node-s6-013-tool-02','node-s6-013-tool-03'],'node-s6-015':['node-s6-015-tool-01','node-s6-015-tool-02','node-s6-015-tool-03'],'node-s6-016':['node-s6-016-tool-01'],'node-s6-018':['node-s6-018-tool-01']}
 for i,n in enumerate(many):
  col=i//4; row=i%4; x=760+col*270; y=1500+row*65; chip(n,x,y,250,42,'#fff')
  for j,t in enumerate(toolmap.get(n,[])): miniasset(t,x+8+j*78,y+45)
 text('section-step-5-label',82,1840,copy['section-step-5'],12,600,'#4a4a4a')
 # terminal downstream chain
 text('section-downstream',60,1920,'Downstream conversion & pipeline velocity',24,900)
 downstream=['node-ds-1','node-ds-2','node-ds-3','node-ds-4']; xs=[65,395,725,1055]
 for i,n in enumerate(downstream):
  fill='#3fe4aa' if n=='node-ds-4' else '#fff'; rect(n,xs[i],1950,280,250,fill,'#242424',18,2); text(n+'-label',xs[i]+18,1986,copy[n],18,800)
  tools=[z for z in usage if z.startswith(n+'-tool')]
  for j,t in enumerate(tools): tile(t,xs[i]+18,2010+j*68,244,56)
  if i<3: path(f'connection-downstream-{i}',f'M {xs[i]+280} 2075 H {xs[i+1]}',dash='6 5',marker='yes')
 # represent explicit architecture connections with non-zero dashed flow strokes, anchored to visual progression.
 for i,con in enumerate(a['connections']):
  cid=con['id']; y=2245+(i%4)*16; x=70+(i//4)*75; path(cid,f'M {x} {y} H {x+48}',stroke='#7c4ddf',dash='3 4',op=.08,marker='yes')
 add('</g></g></g></g></g></g></svg>')
 OUT.mkdir(exist_ok=True); (OUT/'infographic.svg').write_text(''.join(parts),encoding='utf-8')
if __name__=='__main__': main()
