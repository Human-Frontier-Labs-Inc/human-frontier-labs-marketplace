#!/usr/bin/env python3
"""diagram — pictorial wiring diagram from real Fritzing part graphics + colored pin-to-pin
wires. Offline, headless. Board graphics: Fritzing parts library (CC-BY-SA 3.0).
  usage: uv run python3 gen.py <spec.json> [out.png]
Spec: {width,height,title,routing, components:[{id,part,x,y,w?,rotate?,label?}],
       wires:[{from:[id,pin], to:[id,pin], color}], + bus components}
"""
import json, sys, re, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
INDEX = json.loads((PARTS / "index.json").read_text())
COLORS = {"red": "#e5484d", "black": "#222", "yellow": "#e8a733", "green": "#2f9e44",
          "blue": "#1971c2", "orange": "#f76707", "purple": "#7048e8", "violet": "#7048e8",
          "pink": "#e64980", "white": "#ced4da", "gray": "#868e96", "grey": "#868e96",
          "cyan": "#15aabf", "brown": "#a1691a"}

# --- parametric defaults: so a spec only names parts + nets, not sizes/labels ---
# default on-canvas width per part (override with component "w"); keeps parts to scale.
DEFAULT_W = {"ne555": 210, "resistor": 82, "led": 34, "ecap": 46, "npn": 40,
             "pot": 64, "power": 190, "lm386": 210, "speaker": 130, "piezo": 96, "cerc": 44,
             "esp32c3": 150, "st7789": 200, "st7789ada": 215, "inmp441": 96, "button": 50}
# short leg names auto-stamped on multi-pin parts (override per-component with "pinlabels").
PIN_ALIAS = {"vcc supply voltage": "VCC", "voltage common collector": "VCC", "vcc": "VCC",
             "ground": "GND", "gnd": "GND", "discharge": "DIS", "threshold": "THR",
             "trigger": "TRIG", "output": "OUT", "reset": "RST", "control voltage": "CV",
             "wiper": "WIP", "leg1": "L1", "leg2": "L2", "leg3": "L3"}
GENERIC_PINS = {"pin 0", "pin 1", "pin 2", "+", "-", "anode", "cathode"}


def short_pin(name):
    """a compact leg label from a Fritzing connector name (VCC, DIS, TRIG, E/B/C...).
    A compact single token (TFTCS, CARDCS, MOSI, GPIO2) is kept whole — NOT truncated to 4
    chars, which used to garble real pin names. A "canonical (SIGNAL)" name yields the signal."""
    s = name.strip()
    if s.lower() in PIN_ALIAS:
        return PIN_ALIAS[s.lower()]
    m = re.search(r"\(([A-Za-z0-9/]{1,7})\)", s)   # "GPIO 10 (MOSI)" -> MOSI
    if m:
        return m.group(1).upper()
    words = re.split(r"[\s_\-]+", s)
    if len(words) == 1:                            # already a compact token: keep it, cap at 7
        return s.upper()[:7]
    letters = [w[0] for w in words if w and w[0].isalpha()]   # acronym from real words only
    return ("".join(letters) or s).upper()[:5]


def auto_pinlabels(part_id, comp):
    """derive per-leg labels for ICs/transistors/pots (>=3 named legs) unless overridden.
    Set "pinlabels": {} (or false) on a component to suppress labels entirely — e.g. a
    hand-authored board that already prints its pin names on the silkscreen."""
    if "pinlabels" in comp:
        return comp["pinlabels"] or None
    pins = INDEX[part_id]["pins"]
    named = [p for p in pins if p.strip().lower() not in GENERIC_PINS]
    if len(pins) >= 3 and named:
        return {name: short_pin(name) for name in pins}
    return None


def namespace_svg(txt, pfx):
    """prefix every id + its internal references so multiple inlined SVGs don't collide."""
    txt = re.sub(r"<\?xml[^>]*\?>", "", txt)
    txt = re.sub(r"<!DOCTYPE[^>]*>", "", txt)
    for i in sorted(set(re.findall(r'id="([^"]+)"', txt)), key=len, reverse=True):
        txt = (txt.replace(f'id="{i}"', f'id="{pfx}{i}"')
                  .replace(f'#{i}"', f'#{pfx}{i}"')
                  .replace(f"#{i}'", f"#{pfx}{i}'")   # single-quoted refs (xlink:href='#id')
                  .replace(f'#{i})', f'#{pfx}{i})'))
    return txt


def selftest():
    """assert the label-shortener rules that specs now rely on. run: gen.py selftest"""
    cases = {"Vcc Supply Voltage": "VCC", "Ground": "GND", "Discharge": "DIS",
             "Threshold": "THR", "Trigger": "TRIG", "Output": "OUT", "Reset": "RST",
             "Control Voltage": "CV", "E": "E", "B": "B", "anode": "ANODE",
             # compact tokens must survive whole (was the st7789ada TFTCS->TFTC bug)
             "TFTCS": "TFTCS", "TFTRST": "TFTRST", "TFTDC": "TFTDC", "CARDCS": "CARDCS",
             "GPIO 10 (MOSI)": "MOSI", "Chip Select": "CS"}
    for name, want in cases.items():
        got = short_pin(name)
        assert got == want, f"short_pin({name!r}) = {got!r}, want {want!r}"
    # ne555 (8 named legs) auto-labels; a bare resistor (Pin 0/Pin 1) does not
    assert auto_pinlabels("ne555", {})["Threshold"] == "THR"
    assert auto_pinlabels("resistor", {}) is None
    assert auto_pinlabels("ne555", {"pinlabels": {"Reset": "R!"}})["Reset"] == "R!"  # override wins
    print("selftest ok")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        return selftest()
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "diagram.png"
    W, H = spec.get("width", 1200), spec.get("height", 800)
    comps, pinmap, buses = [], {}, {}
    for c in spec["components"]:
        if c["type"] == "bus" if "type" in c else False:
            pass
        if c.get("type") == "bus":
            buses[c["id"]] = {"x1": c["x1"], "x2": c["x2"], "y": c["y"],
                              "label": c.get("label", c["id"]),
                              "color": COLORS.get(c.get("color", "black"), c.get("color", "#222"))}
            continue
        part = INDEX[c["part"]]
        if not part.get("svg"):
            sys.exit(f"SPEC ERROR: part {c['part']!r} (component {c['id']!r}) has no 'svg' in parts/index.json")
        pfx = c["id"] + "__"
        svg = namespace_svg((PARTS / "svg" / part["svg"]).read_text(encoding="utf-8", errors="ignore"), pfx)
        # drop connectors with no resolved terminal id (fritzing.py yields None) so they don't
        # crash pfx+tid; a wire to such a pin is then caught by the validation pass below.
        pinmap[c["id"]] = {name: pfx + tid for name, tid in part["pins"].items() if tid}
        w = c.get("w") or DEFAULT_W.get(c["part"], 90)
        style = f"left:{c['x']}px;top:{c['y']}px;width:{w}px"
        if c.get("rotate"):
            style += f";transform:rotate({c['rotate']}deg)"
        cap = (f'<div class="cap" data-for="{c["id"]}" data-pos="{c.get("labelpos","top")}">{c.get("label","")}</div>'
               if c.get("label") else "")
        comps.append(f'<div class="fzpart" id="{c["id"]}" style="{style}">{svg}</div>{cap}')

    def ep(e):
        return [e[0], e[1] if len(e) > 1 else None]
    wires = []
    for wdef in spec["wires"]:
        fa, fp = ep(wdef["from"])
        ta, tp = ep(wdef["to"])
        wires.append([fa, fp, ta, tp, COLORS.get(wdef.get("color", "black"), wdef.get("color", "#222"))])

    # Fail loud on a mistyped pin or unknown component. A dropped wire is invisible in a
    # headless render, so the diagram would silently omit a connection the author asked for.
    known = set(pinmap) | set(buses)
    errors = []
    for fa, fp, ta, tp, _c in wires:
        for cid, pin in ((fa, fp), (ta, tp)):
            if cid in buses:
                continue
            if cid not in pinmap:
                errors.append(f"wire references unknown component {cid!r} (known ids: {sorted(known)})")
            elif pin is None:
                errors.append(f"wire endpoint [{cid!r}] omits a pin name (only a bus id may do that)")
            elif pin not in pinmap[cid]:
                errors.append(f"component {cid!r} has no pin {pin!r} — valid pins: {sorted(pinmap[cid])}")
    if errors:
        sys.exit("SPEC ERROR — a requested wire can't be drawn:\n  " + "\n  ".join(dict.fromkeys(errors)))

    pinlabels = {}
    for c in spec["components"]:
        if c.get("type") == "bus":
            continue
        lab = auto_pinlabels(c["part"], c)
        if lab:
            pinlabels[c["id"]] = lab
    html = (TEMPLATE.replace("__W__", str(W)).replace("__H__", str(H))
            .replace("__TITLE__", spec.get("title", "")).replace("__ROUTING__", spec.get("routing", "ortho"))
            .replace("__COMPS__", "\n".join(comps)).replace("__PINMAP__", json.dumps(pinmap))
            .replace("__WIRES__", json.dumps(wires)).replace("__BUSES__", json.dumps(buses))
            .replace("__PINLABELS__", json.dumps(pinlabels)))
    tmp = HERE / "_render.html"
    tmp.write_text(html)
    subprocess.run(["chromium", "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--virtual-time-budget=5000",
                    f"--window-size={W},{H}", f"--screenshot={out}", f"file://{tmp}"],
                   check=False, capture_output=True)
    print(f"rendered {out}  ({len(comps)} parts, {len(wires)} wires)")


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
  body{margin:0;background:#f4f1ea;font-family:ui-sans-serif,system-ui}
  #stage{position:relative;width:__W__px;height:__H__px}
  #stage>[id]{position:absolute}
  .fzpart{transform-origin:center}
  .fzpart svg{display:block;width:100%;height:auto;overflow:visible}
  #wires{position:absolute;inset:0;pointer-events:none;overflow:visible;z-index:4}
  h1{position:absolute;left:20px;top:12px;font-size:15px;letter-spacing:1px;color:#3a4a52;margin:0;font-family:ui-monospace,monospace}
  .cap{position:absolute;font-size:11px;color:#33475b;font-family:ui-monospace,monospace;font-weight:700;white-space:nowrap;background:#f7f4ec;border:1px solid #b9b0a0;border-radius:3px;padding:1px 5px;z-index:5}
  .pinlab{position:absolute;font:10px ui-monospace,monospace;font-weight:700;color:#26313d;background:#fff;border:1.5px solid #33475b;border-radius:3px;padding:0 4px;white-space:nowrap;pointer-events:none;z-index:6;line-height:1.45}
  .credit{position:absolute;right:14px;bottom:8px;font:10px ui-monospace,monospace;color:#a49c8c}
</style></head><body>
<div id="stage"><h1>__TITLE__</h1><svg id="wires"></svg>
__COMPS__
<div class="credit">parts: Fritzing (CC-BY-SA)</div>
</div>
<script>
const PINMAP=__PINMAP__, WIRES=__WIRES__, BUSES=__BUSES__, PINLABELS=__PINLABELS__, ROUTING="__ROUTING__";
const NS='http://www.w3.org/2000/svg';
const stage=document.getElementById('stage');
const stageRect=()=>stage.getBoundingClientRect();
function pinPos(id,name){
  const tid=PINMAP[id] && PINMAP[id][name];
  const t=tid && document.getElementById(tid);
  if(!t){console.log('MISSING pin',id,name,tid);return null;}
  const r=t.getBoundingClientRect(), s=stageRect();
  return {x:r.left+r.width/2-s.left, y:r.top+r.height/2-s.top, el:document.getElementById(id)};
}
function endPos(id,pin){ // position of any wire endpoint (part pin, or a bus -> its rail y)
  if(BUSES[id]) return {x:null, y:BUSES[id].y};
  return pinPos(id,pin);
}
// symmetric 2-leg parts (resistors: Pin 0 / Pin 1) are electrically reversible — pick the
// leg->neighbor assignment that DOESN'T make wires double back across the body. Automatic
// so specs never have to hand-order resistor legs.
function autoAssignSymmetric(){
  const symmetric=p=>/^(pin\s*)?\d+$/i.test(p.trim());  // "Pin 0"/"Pin 1", "0"/"1" — non-polar 2-leg parts
  for(const id in PINMAP){
    const pins=Object.keys(PINMAP[id]);
    if(pins.length!==2 || !pins.every(symmetric)) continue;  // skip polar parts (+/-, anode/cathode)
    const [k0,k1]=pins;
    const el=document.getElementById(id); if(!el) continue;
    const cx=el.getBoundingClientRect().left-stageRect().left;
    const centroid=(pn)=>{const xs=[],ys=[];
      for(const [a,ap,b,bp] of WIRES){let o=null;
        if(a===id&&ap===pn)o=endPos(b,bp); else if(b===id&&bp===pn)o=endPos(a,ap);
        if(o){xs.push(o.x==null?cx:o.x);ys.push(o.y);}}
      if(!xs.length)return null;
      return {x:xs.reduce((s,v)=>s+v,0)/xs.length,y:ys.reduce((s,v)=>s+v,0)/ys.length};};
    const o0=centroid(k0),o1=centroid(k1),p0=pinPos(id,k0),p1=pinPos(id,k1);
    if(!o0||!o1||!p0||!p1) continue;
    const d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
    if(d(p0,o1)+d(p1,o0) < d(p0,o0)+d(p1,o1)-1){
      const t=PINMAP[id][k0];PINMAP[id][k0]=PINMAP[id][k1];PINMAP[id][k1]=t;}
  }
}
function exitDir(el,p){
  const r=el.getBoundingClientRect(), s=stageRect();
  const bx=r.left-s.left, by=r.top-s.top;
  const dl=p.x-bx, dr=(bx+r.width)-p.x, dt=p.y-by, db=(by+r.height)-p.y;
  const m=Math.min(dl,dr,dt,db);
  if(m===dl)return{x:-1,y:0}; if(m===dr)return{x:1,y:0}; if(m===dt)return{x:0,y:-1}; return{x:0,y:1};
}
function curvePath(p1,p2){const dx=Math.max(30,Math.abs(p2.x-p1.x)*0.4);
  return `M ${p1.x} ${p1.y} C ${p1.x+dx} ${p1.y}, ${p2.x-dx} ${p2.y}, ${p2.x} ${p2.y}`;}
function dir(a,b){const dx=b.x-a.x,dy=b.y-a.y,l=Math.hypot(dx,dy)||1;return{x:dx/l,y:dy/l};}
function roundedPath(pts,r){let d=`M ${pts[0].x} ${pts[0].y}`;
  for(let i=1;i<pts.length-1;i++){const b=pts[i],di=dir(b,pts[i-1]),dou=dir(b,pts[i+1]);
    const rr=Math.min(r,Math.hypot(pts[i-1].x-b.x,pts[i-1].y-b.y)/2,Math.hypot(pts[i+1].x-b.x,pts[i+1].y-b.y)/2);
    d+=` L ${b.x+di.x*rr} ${b.y+di.y*rr} Q ${b.x} ${b.y} ${b.x+dou.x*rr} ${b.y+dou.y*rr}`;}
  const last=pts[pts.length-1];return d+` L ${last.x} ${last.y}`;}
// --- obstacle-aware ortho routing: try candidate paths, pick the one crossing fewest parts ---
let BOXES=[];
function collectBoxes(){BOXES=[];const s=stageRect();
  document.querySelectorAll('.fzpart').forEach(el=>{const r=el.getBoundingClientRect();
    BOXES.push({x:r.left-s.left,y:r.top-s.top,w:r.width,h:r.height});});}
function segHits(a,b){let n=0;const pad=4;
  for(const bx of BOXES){const x1=bx.x-pad,x2=bx.x+bx.w+pad,y1=bx.y-pad,y2=bx.y+bx.h+pad;
    if(Math.abs(a.x-b.x)<0.5){if(a.x>x1&&a.x<x2&&Math.min(a.y,b.y)<y2-1&&Math.max(a.y,b.y)>y1+1)n++;}
    else{if(a.y>y1&&a.y<y2&&Math.min(a.x,b.x)<x2-1&&Math.max(a.x,b.x)>x1+1)n++;}}
  return n;}
function cost(pts){let h=0,l=0;for(let i=0;i<pts.length-1;i++){h+=segHits(pts[i],pts[i+1]);
    l+=Math.abs(pts[i].x-pts[i+1].x)+Math.abs(pts[i].y-pts[i+1].y);}
  return h*100000+l+pts.length*40;}
function bounds(){let L=1e9,R=-1e9,T=1e9,B=-1e9;for(const b of BOXES){
    L=Math.min(L,b.x);R=Math.max(R,b.x+b.w);T=Math.min(T,b.y);B=Math.max(B,b.y+b.h);}return{L,R,T,B};}
function route(p1,d1,p2,d2,i){const L=22, lane=((i%11)-5)*4;   // per-wire lane so parallel runs don't overlap (11 lanes)
  const s1={x:p1.x+d1.x*L,y:p1.y+d1.y*L}, s2={x:p2.x+d2.x*L,y:p2.y+d2.y*L};
  const v1=Math.abs(d1.x)<0.5, v2=Math.abs(d2.x)<0.5, bb=bounds(), cand=[];
  if(v1&&v2){                       // both exit vertically: horizontal trunk, or route around a side
    const ys=[(s1.y+s2.y)/2+lane, Math.min(s1.y,s2.y)-30+lane, Math.max(s1.y,s2.y)+30+lane];
    for(const b of BOXES){ys.push(b.y-10+lane,b.y+b.h+10+lane);}
    for(const Y of ys) cand.push([p1,s1,{x:s1.x,y:Y},{x:s2.x,y:Y},s2,p2]);
    const xs=[bb.L-30+lane,bb.R+30+lane]; for(const b of BOXES){xs.push(b.x-10+lane,b.x+b.w+10+lane);}
    for(const X of xs) cand.push([p1,s1,{x:X,y:s1.y},{x:X,y:s2.y},s2,p2]);
  }else if(!v1&&!v2){               // both exit horizontally: vertical trunk, or route over/under
    const xs=[(s1.x+s2.x)/2+lane, Math.min(s1.x,s2.x)-30+lane, Math.max(s1.x,s2.x)+30+lane];
    for(const b of BOXES){xs.push(b.x-10+lane,b.x+b.w+10+lane);}
    for(const X of xs) cand.push([p1,s1,{x:X,y:s1.y},{x:X,y:s2.y},s2,p2]);
    const ys=[bb.T-30+lane,bb.B+30+lane]; for(const b of BOXES){ys.push(b.y-10+lane,b.y+b.h+10+lane);}
    for(const Y of ys) cand.push([p1,s1,{x:s1.x,y:Y},{x:s2.x,y:Y},s2,p2]);
  }else{                            // mixed: L-elbow (two corners) or a mid-channel detour
    cand.push([p1,s1,{x:s1.x,y:s2.y},s2,p2],[p1,s1,{x:s2.x,y:s1.y},s2,p2]);
    const mx=(s1.x+s2.x)/2+lane,my=(s1.y+s2.y)/2+lane;
    cand.push([p1,s1,{x:mx,y:s1.y},{x:mx,y:s2.y},s2,p2],[p1,s1,{x:s1.x,y:my},{x:s2.x,y:my},s2,p2]);
  }
  let best=cand[0],bc=Infinity;
  for(const c of cand){const k=cost(c);if(k<bc){bc=k;best=c;}}
  const clean=best.filter((p,i)=>i===0||p.x!==best[i-1].x||p.y!==best[i-1].y);
  return roundedPath(clean,7);}
function busTap(b,pin){const lo=Math.min(b.x1,b.x2),hi=Math.max(b.x1,b.x2);const bx=Math.max(lo,Math.min(hi,pin.x));
  return {x:bx,y:b.y,d:{x:0,y:pin.y<b.y?-1:1}};}
function draw(){
  const svg=document.getElementById('wires'), n=WIRES.length;
  collectBoxes();
  autoAssignSymmetric();
  for(const id in BUSES){const b=BUSES[id];
    const rail=document.createElementNS(NS,'path');rail.setAttribute('d',`M ${b.x1} ${b.y} L ${b.x2} ${b.y}`);
    rail.setAttribute('stroke',b.color);rail.setAttribute('stroke-width','5');rail.setAttribute('stroke-linecap','round');rail.setAttribute('fill','none');svg.appendChild(rail);
    const lab=document.createElement('div');lab.className='cap';lab.textContent=b.label;stage.appendChild(lab);
    lab.style.left=b.x1+'px';lab.style.top=b.y+'px';lab.style.transform='translate(-100%,-50%)';}
  WIRES.forEach(([a,ap,b,bp,color],i)=>{
    let p1,p2,d1,d2; const aB=BUSES[a], bB=BUSES[b];
    if(aB&&bB){ // rail-to-rail: straight vertical link where the two rails overlap in x
      const lo=Math.max(Math.min(aB.x1,aB.x2),Math.min(bB.x1,bB.x2));
      const hi=Math.min(Math.max(aB.x1,aB.x2),Math.max(bB.x1,bB.x2));
      const x=lo<=hi?(lo+hi)/2:Math.min(aB.x1,aB.x2);
      p1={x,y:aB.y};p2={x,y:bB.y};d1={x:0,y:bB.y>aB.y?1:-1};d2={x:0,y:aB.y>bB.y?1:-1};}
    else if(bB){p1=pinPos(a,ap);if(!p1)return;d1=exitDir(p1.el,p1);const t=busTap(bB,p1);p2={x:t.x,y:t.y};d2=t.d;}
    else if(aB){p2=pinPos(b,bp);if(!p2)return;d2=exitDir(p2.el,p2);const t=busTap(aB,p2);p1={x:t.x,y:t.y};d1=t.d;}
    else{p1=pinPos(a,ap);p2=pinPos(b,bp);if(!p1||!p2)return;d1=exitDir(p1.el,p1);d2=exitDir(p2.el,p2);}
    const path=document.createElementNS(NS,'path');
    path.setAttribute('d',ROUTING==="curve"?curvePath(p1,p2):route(p1,d1,p2,d2,i));
    path.setAttribute('stroke',color);path.setAttribute('stroke-width','3.4');path.setAttribute('fill','none');
    path.setAttribute('stroke-linecap','round');path.setAttribute('stroke-linejoin','round');svg.appendChild(path);
    for(const p of [p1,p2]){const c=document.createElementNS(NS,'circle');
      c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r','3.6');c.setAttribute('fill',color);svg.appendChild(c);}
  });
  const _pl=new Set();
  WIRES.forEach(([a,ap,b,bp])=>{
    for(const [id,name] of [[a,ap],[b,bp]]){
      if(!PINLABELS[id]||!PINLABELS[id][name])continue;
      const k=id+'/'+name; if(_pl.has(k))continue; _pl.add(k);
      const p=pinPos(id,name); if(!p)continue; const d=exitDir(p.el,p);
      const lab=document.createElement('div');lab.className='pinlab';lab.textContent=PINLABELS[id][name];
      stage.appendChild(lab);
      lab.style.left=(p.x+d.x*12)+'px';lab.style.top=(p.y+d.y*12)+'px';
      const tx=d.x<0?-100:d.x>0?0:-50,ty=d.y<0?-100:d.y>0?0:-50;
      lab.style.transform=`translate(${tx}%,${ty}%)`;
    }
  });
  document.querySelectorAll('.cap[data-for]').forEach(cap=>{
    const el=document.getElementById(cap.dataset.for),r=el.getBoundingClientRect(),s=stageRect();
    const cw=cap.offsetWidth,ch=cap.offsetHeight,cx=r.left-s.left,cy=r.top-s.top,W=r.width,Hh=r.height;
    const pos=cap.dataset.pos||'top'; let L,T;
    if(pos==='bottom'){L=cx+W/2-cw/2;T=cy+Hh+6;}
    else if(pos==='left'){L=cx-cw-8;T=cy+Hh/2-ch/2;}
    else if(pos==='right'){L=cx+W+8;T=cy+Hh/2-ch/2;}
    else {L=cx+W/2-cw/2;T=cy-ch-6;}
    cap.style.left=L+'px';cap.style.top=T+'px';});
  document.title='READY';
}
window.addEventListener('load',()=>setTimeout(draw,200));
</script></body></html>
"""

if __name__ == "__main__":
    main()
