"""Assemble clip fragments + engine + fonts + brand into self-contained HTML files.
usage: python3 build.py <out_dir> clips/01-name.html [clips/02-name.html ...] [--brand trailgoat|default|path/to/brand_dir]

The brand (default: $KB_YTVIDEO_BRAND or 'trailgoat') supplies CSS variables (--canvas, --panel, --ink, --accent,
--c-fuel ..., --f-display, --f-text, --f-mono), a window.BRAND object for clip scripts, embedded fonts, and assets:
write src="brand:wordmark" (or url(brand:topo-16x9)) in a fragment and it becomes an embedded data URI.
'default' keeps the upstream motion-broll look (warm gray, black, orange, Geist)."""
import base64, json, os, re, sys, pathlib
E = pathlib.Path(__file__).resolve().parent
SKILL = E.parent
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp'}
FONT_FMT = {'.ttf': ('font/ttf', 'truetype'), '.otf': ('font/otf', 'opentype'), '.woff2': ('font/woff2', 'woff2')}
DEFAULT = {'name': 'default', 'colors': {'canvas': '#E9E7E2', 'well': '#DCD9D2', 'panel': '#FFFFFF', 'raised': '#F4F2EE',
           'ink': '#0B0B0B', 'bright': '#0B0B0B', 'muted': '#6B6862', 'line': '#D6D3CC', 'accent': '#FF5A1F', 'accentInk': '#FFFFFF'},
           'data': {}, 'fonts': {'display': {'family': 'Geist'}, 'text': {'family': 'Geist'}, 'mono': {'family': 'Geist Mono'}}, 'assets': {}}

def load_brand(name):
    if name == 'default': return DEFAULT, None
    d = pathlib.Path(name) if os.sep in name or pathlib.Path(name).is_dir() else SKILL / 'brands' / name
    return json.load(open(d / 'brand.json')), d

def brand_css(B, d):
    css = []
    for role, f in B['fonts'].items():
        if 'file' not in f: continue
        p = d / f['file'] if (d and (d / f['file']).exists()) else E / 'fonts' / f['file']
        mime, fmt = FONT_FMT[p.suffix.lower()]
        css.append(f"@font-face{{font-family:'{f['family']}';src:url(data:{mime};base64,{b64(p)}) format('{fmt}');font-weight:{f.get('weight', '100 900')}}}")
    kebab = lambda k: re.sub(r'([A-Z])', lambda m: '-' + m.group(1).lower(), k)
    v = [f'--{kebab(k)}:{c}' for k, c in B['colors'].items()] + [f'--c-{k}:{c}' for k, c in B.get('data', {}).items()]
    fam = lambda r, fb: f"'{B['fonts'][r]['family']}',{fb}"
    v += [f"--f-display:{fam('display', 'system-ui,sans-serif')}", f"--f-text:{fam('text', 'system-ui,sans-serif')}", f"--f-mono:{fam('mono', 'ui-monospace,monospace')}"]
    css.append(':root{' + ';'.join(v) + '}')
    return ''.join(css)

def inline_assets(s, B, d):
    def rep(m):
        key = m.group(1); f = B.get('assets', {}).get(key)
        if not f or not d: sys.exit(f'build.py: brand asset "{key}" not found in brand {B["name"]}')
        p = d / f; return f'data:{MIME[p.suffix.lower()]};base64,{b64(p)}'
    return re.sub(r'brand:([A-Za-z0-9_-]+)', rep, s)

CURSOR = '<svg id="cursor" viewBox="0 0 40 56"><path d="M3 3 L3 41 L12.5 32 L19 47 L25.5 44.2 L19.2 29.8 L32 29.8 Z" fill="#0B0B0B" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/></svg>'

def build(src, dst, B, d):
    frag = open(src, encoding='utf-8').read()
    m = re.search(r'<title>(.*?)</title>', frag); title = m.group(1) if m else pathlib.Path(src).stem
    css = ''.join(re.findall(r'<style>(.*?)</style>', frag, re.S))
    slot = lambda n: (re.search(rf'<div data-slot="{n}">(.*?)</div><!--/{n}-->', frag, re.S) or [None, ''])[1]
    js = ''.join(re.findall(r'<script>(.*?)</script>', frag, re.S))
    base = open(E / 'base.css').read().replace('__GEIST__', b64(E / 'fonts/Geist-Variable.woff2')).replace('__GEISTMONO__', b64(E / 'fonts/GeistMono-Medium.woff2'))
    brand_js = 'window.BRAND=' + json.dumps({'name': B['name'], **B['colors'], 'data': B.get('data', {})}) + ';'
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>{base}{brand_css(B, d)}{css}</style></head><body>\n'
            f'<div id="wrap"><div id="stage"><div id="world">{slot("world")}<div id="shape">{slot("shape")}</div>{slot("over")}</div>{slot("hud")}{CURSOR}</div></div>\n'
            f'<script>{brand_js}</script><script>{open(E / "motion.js").read()}</script><script>{js}</script></body></html>')
    open(dst, 'w', encoding='utf-8').write(inline_assets(html, B, d))

if __name__ == '__main__':
    args = sys.argv[1:]; brand = os.environ.get('KB_YTVIDEO_BRAND', 'trailgoat')
    if '--brand' in args: i = args.index('--brand'); brand = args[i + 1]; del args[i:i + 2]
    B, d = load_brand(brand)
    out = pathlib.Path(args[0]); out.mkdir(parents=True, exist_ok=True)
    for s in args[1:]:
        dst = out / (pathlib.Path(s).stem + '.html'); build(s, dst, B, d); print('built', dst, f'(brand: {B["name"]})')
