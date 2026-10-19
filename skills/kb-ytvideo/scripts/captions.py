"""Word-timed social captions as a transparent clip fragment (build + render it like any clip -> ProRes 4444 .mov).
usage: python3 captions.py words.txt clips/90-captions.html --size 1080x1920 [--from 0 --to 60] [--offset 0]
        [--words 3] [--chars 18] [--y 0.66] [--px 86] [--style pop|karaoke] [--upper]
- Pages break at each transcript line (segment), sentence punctuation, pauses over 0.45 s, or the word/char limit.
- Active word takes the brand accent; 'pop' also springs it up slightly. 'karaoke' keeps earlier words lit.
- --from/--to pick a window of the source (seconds); clip time 0 = --from. --offset shifts all words (+ later).
- --y is the caption centre as a fraction of height. Defaults keep clear of TikTok/Reels/Shorts UI (see reference/platforms.md)."""
import argparse, json, re
ap = argparse.ArgumentParser(); ap.add_argument('words'); ap.add_argument('out')
ap.add_argument('--size', default='1080x1920'); ap.add_argument('--fps', default=None)
ap.add_argument('--from', dest='t0', type=float, default=0); ap.add_argument('--to', dest='t1', type=float, default=None)
ap.add_argument('--offset', type=float, default=0); ap.add_argument('--words', dest='nwords', type=int, default=None); ap.add_argument('--chars', type=int, default=None)
ap.add_argument('--y', type=float, default=None); ap.add_argument('--px', type=int, default=None)
ap.add_argument('--style', default='pop', choices=['pop', 'karaoke']); ap.add_argument('--upper', action='store_true')
a = ap.parse_args(); W, H = map(int, a.size.split('x')); vertical = H > W
nw = a.nwords or (3 if vertical else 7); nc = a.chars or (18 if vertical else 42)
y = a.y if a.y is not None else (0.66 if vertical else 0.86); px = a.px or (86 if vertical else 56)
toks = []
for line in open(a.words, encoding='utf-8'):
    first = True
    for tok in line.split():
        m = re.match(r'([\d.]+)(?:-([\d.]+))?:(.+)', tok)
        if not m: continue
        s = float(m.group(1)) + a.offset; e = float(m.group(2)) + a.offset if m.group(2) else None
        toks.append([s, e, m.group(3), first]); first = False
for i, t in enumerate(toks):
    if t[1] is None: t[1] = toks[i + 1][0] if i + 1 < len(toks) else t[0] + 0.4
t1 = a.t1 if a.t1 is not None else (toks[-1][1] + 0.5 if toks else 1)
toks = [[s - a.t0, e - a.t0, w, seg] for s, e, w, seg in toks if s >= a.t0 and s < t1]
pages, cur = [], []
for i, t in enumerate(toks):
    gap = t[0] - cur[-1][1] if cur else 0
    # a new transcript line (segment) always starts a new page, as does a pause or the word/char limit
    if cur and (t[3] or len(cur) >= nw or len(' '.join(x[2] for x in cur + [t])) > nc or gap > 0.45):
        pages.append(cur); cur = []
    cur.append(t)
    if re.search(r'[.!?]$', t[2]): pages.append(cur); cur = []
if cur: pages.append(cur)
P = []
for i, p in enumerate(pages):
    start = p[0][0] - 0.06; nxt = pages[i + 1][0][0] - 0.06 if i + 1 < len(pages) else None
    end = p[-1][1] + 0.25; end = min(end, nxt) if nxt is not None else end
    P.append({'a': round(max(0, start), 3), 'b': round(end, 3), 'w': [[round(x[0], 3), (x[2].upper() if a.upper else x[2])] for x in p]})
T = round(t1 - a.t0, 2)
frag = f"""<title>Captions {a.t0:.1f}-{t1:.1f}s</title>
<style>
#cap{{position:absolute;left:0;right:0;top:{y * 100:.2f}%;transform:translateY(-50%);text-align:center;padding:0 {int(W * 0.08)}px}}
.pg{{position:absolute;left:{int(W * 0.08)}px;right:{int(W * 0.08)}px;top:0;transform:translateY(-50%);display:flex;flex-wrap:wrap;justify-content:center;gap:0 .3em;
 font:800 {px}px/1.08 var(--f-display);letter-spacing:-0.01em;color:var(--bright);
 -webkit-text-stroke:{max(6, px // 9)}px var(--well);paint-order:stroke fill}}
.w{{display:inline-block;transform-origin:50% 70%}}
</style>
<div data-slot="world"></div><!--/world-->
<div data-slot="shape"></div><!--/shape-->
<div data-slot="hud"><div id="cap"></div></div><!--/hud-->
<script>
const PAGES={json.dumps(P, ensure_ascii=False)}, STYLE='{a.style}';
const cap=document.getElementById('cap');
const nodes=PAGES.map(p=>{{const d=document.createElement('div');d.className='pg';
  p.els=p.w.map(([s,w])=>{{const e=document.createElement('span');e.className='w';e.textContent=w;d.appendChild(e);return e;}});cap.appendChild(d);return d;}});
M.scene({{W:{W},H:{H},T:{T},bg:null,intro:null,SH:{{c:{{w:0,h:0,r:0,bg:'#000000',cam:1}}}},start:'c',SEQ:[],
 extra:(t)=>{{
  PAGES.forEach((p,i)=>{{
   const v=M.vis(t,p.a,p.b,{{din:0.03,lin:0.12,lout:0.06,blur:6}});
   if(!M.apply(nodes[i],v,'')) return; nodes[i].style.transform=`translateY(-50%) scale(${{v.s.toFixed(4)}})`;
   p.w.forEach(([s],k)=>{{const e=p.els[k], nx=k+1<p.w.length?p.w[k+1][0]:p.b, on=t>=s&&t<nx, lit=STYLE==='karaoke'?t>=s:on;
     e.style.color=lit?BRAND.accent:'';
     const k0=M.S(t-s,26,0.55)-M.S(t-nx,20,0.9); e.style.transform=STYLE==='pop'?`translateY(${{(-5*k0).toFixed(2)}}px) scale(${{(1+0.035*k0).toFixed(4)}})`:'';}});
  }});
 }}}});
</script>
"""
open(a.out, 'w', encoding='utf-8').write(frag)
print(f'wrote {a.out}: {len(P)} caption pages, {T}s, {W}x{H}, transparent -> render to .mov')
